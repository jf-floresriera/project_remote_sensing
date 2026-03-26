// ============================================================
// SCRIPT 1 COMPLETO: GPR LAI - Meta 2023 - 40 imágenes
// Salinero-Delgado et al. (2022) Remote Sensing
// ============================================================

// === MODELOS GPR del artículo (NO TOCAR) ===
var importedModels = require('users/msalinero85/GPRPhenologyDemos:S2BOAModels');
var currentVegIndex = 'LAI';
var currentModel = importedModels.models[currentVegIndex];

// === CONFIGURACIÓN ===
var region = ee.Geometry.Rectangle([-72.062937, 4.206600, -71.492754, 4.5]);
var ASSET_FOLDER = 'projects/wide-origin-466923-d8/assets/GPR_LAI_meta_2023';

// === MÁSCARA DE NUBES (CORREGIDA) ===
function maskS2cloud_and_water(image) {
  var scl = image.select('SCL');
  var qa  = image.select('QA60');

  var mask = scl.neq(1).and(scl.neq(2)).and(scl.neq(3))
    .and(scl.neq(6)).and(scl.neq(7)).and(scl.neq(8))
    .and(scl.neq(9)).and(scl.neq(10)).and(scl.neq(11))
    .and(qa.bitwiseAnd(1 << 10).eq(0))
    .and(qa.bitwiseAnd(1 << 11).eq(0));

  return image.updateMask(mask)
    .divide(currentModel.scaleFactor)
    .set('system:time_start', image.get('system:time_start'))
    .set('system:index', image.get('system:index'));
}

// === FUNCIÓN GPR (exactamente del artículo) ===
var veg_index_GPR = function(image_orig) {
  var XTrain_dim = currentModel.X_train.length().get([0]);
  var band_sequence = ee.List.sequence(1, XTrain_dim).map(function(element) {
    return ee.String('B').cat(ee.String(element)).replace('[.]+[0-9]*$', '');
  });

  var im_norm_ell2D_hypell = image_orig
    .subtract(ee.Image(currentModel.mx))
    .divide(ee.Image(currentModel.sx))
    .multiply(ee.Image(currentModel.hyp_ell))
    .toArray().toArray(1);

  var im_norm_ell2D = image_orig
    .subtract(ee.Image(currentModel.mx))
    .divide(ee.Image(currentModel.sx))
    .toArray().toArray(1);

  var PtTPt = im_norm_ell2D_hypell.matrixTranspose()
    .matrixMultiply(im_norm_ell2D).arrayProject([0]).multiply(-0.5);

  var PtTDX = ee.Image(currentModel.X_train)
    .matrixMultiply(im_norm_ell2D_hypell)
    .arrayProject([0]).arrayFlatten([band_sequence]);

  var arg1   = PtTPt.exp().multiply(currentModel.hyp_sig);
  var k_star = PtTDX.subtract(
    ee.Image(currentModel.XDX_pre_calc).multiply(0.5)).exp().toArray();

  var mean_pred = k_star
    .arrayDotProduct(ee.Image(currentModel.alpha_coefficients).toArray())
    .multiply(arg1);

  mean_pred = mean_pred.toArray(1).arrayProject([0])
    .arrayFlatten([[currentModel.veg_index]]);
  mean_pred = mean_pred.add(currentModel.mean_model);
  mean_pred = mean_pred.where(mean_pred.lt(0), ee.Image(0.00001));

  return image_orig.addBands(mean_pred)
    .select(currentModel.veg_index)
    .toFloat();
};

// === COLECCIÓN 40 IMÁGENES ===
var col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filter(ee.Filter.eq('MGRS_TILE', '18NZK'))
  .filterBounds(region)
  .filterDate('2023-01-01', '2023-12-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 80));

print('Total imágenes a exportar:', col.size()); // 40

// === LOOP: EXPORTAR LAS 40 IMÁGENES ===
var imageList = col.toList(col.size());
var total = col.size().getInfo(); // trae el número al cliente

for (var i = 0; i < total; i++) {

  var img = ee.Image(imageList.get(i));

  // Seleccionar bandas necesarias + máscaras
  var imgBands = img.select(
    ['B2','B3','B4','B5','B6','B7','B8','B8A','B11','B12','QA60','SCL']
  );

  // Aplicar máscara y normalizar
  var imgMasked = maskS2cloud_and_water(imgBands)
    .select(['B2','B3','B4','B5','B6','B7','B8','B8A','B11','B12']);

  // Aplicar modelo GPR
  var imgLAI = veg_index_GPR(imgMasked).clip(region);

  // Obtener fecha para nombre del asset
  var fecha = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd');

  // Exportar como asset
  Export.image.toAsset({
    image: imgLAI,
    description: 'LAI_' + fecha.getInfo(),
    assetId: ASSET_FOLDER + '/LAI_' + fecha.getInfo(),
    region: region,
    scale: 20,
    crs: 'EPSG:4326',
    maxPixels: 1e9
  });
}

print('✅ ' + total + ' tasks listas para lanzar en el panel Tasks →');
print('👉 Ve a Tasks (arriba derecha) y haz clic en RUN ALL');
