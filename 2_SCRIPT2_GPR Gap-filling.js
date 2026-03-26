// ============================================================
// SCRIPT 2: GPR Gap-filling SOLO EN POLÍGONOS - Meta 2023
// VERSIÓN SEGURA: Salta las tareas que ya existen/corrieron
// ============================================================

// Usando tu módulo guardado localmente:
var importedModels = require('users/jfloresr/project_1:S2BOAModels');

var vegIndices = ['LAI', 'FVC', 'laiCab'];

var region = ee.Geometry.Rectangle([-72.062937, 4.206600, -71.492754, 4.5]);
var parcelas = ee.FeatureCollection('projects/wide-origin-466923-d8/assets/maiz_industrial_meta_2023')
                 .filterBounds(region);
var parcelasMask = ee.Image.constant(0).clip(region).paint(parcelas, 1);

var addVariables = function(image) {
  var days = ee.Date(image.get('system:time_start')).difference(ee.Date('1970-01-01'), 'days');
  return image.addBands(ee.Image(days).rename('t').float())
              .set('system:time_start', image.get('system:time_start'));
};

vegIndices.forEach(function(currentVegIndex) {
  
  var currentModel = importedModels.models[currentVegIndex];

  var ell2_ts = currentModel.gf_hyperparams['media'].ell2_ts;
  var sigf_ts = currentModel.gf_hyperparams['media'].sigf_ts;
  var sign_ts = currentModel.gf_hyperparams['media'].sign_ts;

  var ASSET_FOLDER_IN  = 'projects/wide-origin-466923-d8/assets/GPR_' + currentVegIndex + '_meta_2023';
  var ASSET_FOLDER_OUT = 'projects/wide-origin-466923-d8/assets/GPR_' + currentVegIndex + '_meta_2023_gapfilled';

  function maskS2cloud_and_water(image) {
    var scl = image.select('SCL');
    var qa  = image.select('QA60');
    var mask = scl.neq(1).and(scl.neq(2)).and(scl.neq(3))
      .and(scl.neq(6)).and(scl.neq(7)).and(scl.neq(8))
      .and(scl.neq(9)).and(scl.neq(10)).and(scl.neq(11))
      .and(qa.bitwiseAnd(1 << 10).eq(0)).and(qa.bitwiseAnd(1 << 11).eq(0));
    return image.updateMask(mask).divide(currentModel.scaleFactor)
                .set('system:time_start', image.get('system:time_start'));
  }

  var veg_index_GPR = function(image_orig) {
    var XTrain_dim = currentModel.X_train.length().get([0]);
    var band_sequence = ee.List.sequence(1, XTrain_dim).map(function(element) {
      return ee.String('B').cat(ee.String(element)).replace('[.]+[0-9]*$', '');
    });
    var im_norm_ell2D_hypell = image_orig.subtract(ee.Image(currentModel.mx)).divide(ee.Image(currentModel.sx)).multiply(ee.Image(currentModel.hyp_ell)).toArray().toArray(1);
    var im_norm_ell2D = image_orig.subtract(ee.Image(currentModel.mx)).divide(ee.Image(currentModel.sx)).toArray().toArray(1);
    var PtTPt = im_norm_ell2D_hypell.matrixTranspose().matrixMultiply(im_norm_ell2D).arrayProject([0]).multiply(-0.5);
    var PtTDX = ee.Image(currentModel.X_train).matrixMultiply(im_norm_ell2D_hypell).arrayProject([0]).arrayFlatten([band_sequence]);
    var arg1   = PtTPt.exp().multiply(currentModel.hyp_sig);
    var k_star = PtTDX.subtract(ee.Image(currentModel.XDX_pre_calc).multiply(0.5)).exp().toArray();
    var mean_pred = k_star.arrayDotProduct(ee.Image(currentModel.alpha_coefficients).toArray()).multiply(arg1);
    mean_pred = mean_pred.toArray(1).arrayProject([0]).arrayFlatten([[currentModel.veg_index]]);
    mean_pred = mean_pred.add(currentModel.mean_model);
    mean_pred = mean_pred.where(mean_pred.lt(0), ee.Image(0.00001));
    return image_orig.addBands(mean_pred).select(currentModel.veg_index).toFloat();
  };

  var calculate_gapfilling = function(image) {
    var imageDate          = ee.Date(image.get('system:time_start'));
    var dateOfInterest     = imageDate.format('YYYY-MM-dd');
    var Date_Start_str     = ee.Date(dateOfInterest).advance(-30, 'day');
    var Date_End_str       = ee.Date(dateOfInterest).advance(30, 'day');
    var dateOfInterest_num = ee.Date(dateOfInterest).difference(ee.Date('1970-01-01'), 'days');

    var veg_col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(region)
      .filterDate(Date_Start_str, Date_End_str)
      .filter(ee.Filter.eq('MGRS_TILE', '18NZK'))
      .map(maskS2cloud_and_water)
      .select(['B2','B3','B4','B5','B6','B7','B8','B8A','B11','B12'])
      .map(function(img) { return img.updateMask(parcelasMask); })
      .map(veg_index_GPR);

    var veg_col_mask = veg_col.map(function(img) {
      return img.select(currentModel.veg_index).gt(0).rename('veg_index_mask');
    });

    var time_im        = veg_col.map(addVariables).select('t');
    var t_star_vec     = time_im.first().multiply(0).add(dateOfInterest_num).toArray().toArray(1);
    var Nsize          = time_im.size();

    var t_vec_sel      = veg_col_mask.toBands().multiply(time_im.toBands()).unmask().toArray().toArray(1);
    var lai_vec        = veg_col.toBands().unmask().toArray().toArray(1);

    var ones_vec_sel   = t_vec_sel.multiply(0).add(1.0);
    var ones_vec_star  = t_star_vec.multiply(0).add(1.0);

    var II_mat         = ee.Image(ee.Array.identity(Nsize));
    var prod           = t_vec_sel.matrixMultiply(ones_vec_sel.matrixTranspose());
    var K_mat          = prod.subtract(prod.matrixTranspose()).pow(2).multiply(ell2_ts).multiply(-0.5).exp().multiply(sigf_ts);

    var L_mat          = II_mat.multiply(sign_ts).add(K_mat).matrixCholeskyDecomposition();
    var alpha_vec      = L_mat.matrixTranspose().matrixInverse().matrixMultiply(L_mat.matrixInverse().matrixMultiply(lai_vec));

    var t_star_mat     = t_star_vec.matrixMultiply(ones_vec_sel.matrixTranspose());
    var t_train_mat    = t_vec_sel.matrixMultiply(ones_vec_star.matrixTranspose()).matrixTranspose();
    var k_star_mat     = t_star_mat.subtract(t_train_mat).pow(2).multiply(ell2_ts).multiply(-0.5).exp().multiply(sigf_ts);

    var pred_vec       = k_star_mat.matrixMultiply(alpha_vec).arrayProject([0]).arrayFlatten([['gapfilled']]).toFloat();
    pred_vec = pred_vec.where(pred_vec.lt(0), ee.Image(0.00001)).toFloat();

    return image.addBands(pred_vec).select('gapfilled').updateMask(parcelasMask)
      .set('system:time_start', image.get('system:time_start'));
  };

  var colAssetsList;
  try {
    colAssetsList = ee.data.listAssets(ASSET_FOLDER_IN).assets;
  } catch(e) {
    print('Error leyendo la carpeta: ' + ASSET_FOLDER_IN);
    return;
  }

  var imageCollection = ee.ImageCollection(colAssetsList.map(function(asset) { return ee.Image(asset.id); }));
  var imageList = imageCollection.toList(imageCollection.size());
  var total     = imageCollection.size().getInfo();
  
  var tareasLanzadas = 0;

  for (var i = 0; i < total; i++) {
    var img   = ee.Image(imageList.get(i));
    var fecha = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd').getInfo();
    
    var assetDestino = ASSET_FOLDER_OUT + '/' + currentVegIndex + '_gf_' + fecha;
    
    // COMPROBACIÓN: Solo crea la tarea si el archivo NO existe en la carpeta destino
    try {
      ee.data.getAsset(assetDestino);
      print('Saltando (ya existe): ' + assetDestino);
    } catch (e) {
      // Si entra al catch, significa que NO existe, así que lo preparamos para exportar
      var imgGF = calculate_gapfilling(img).clip(region);
      
      Export.image.toAsset({
        image: imgGF,
        description: currentVegIndex + '_gf_' + fecha,
        assetId: assetDestino,
        region: region,
        scale: 20,
        crs: 'EPSG:4326',
        maxPixels: 1e9
      });
      tareasLanzadas++;
    }
  }
  print(currentVegIndex + ' -> Tareas nuevas para lanzar: ' + tareasLanzadas);
});

print('✅ Tareas pendientes listas en la pestaña Tasks. ¡Dale a Run All!');
