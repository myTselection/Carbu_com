"""Constants for Gas Station Spain."""

DOMAIN = "gas_station_spain"
PROVINCES_ENDPOINT = "https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/Listados/Provincias"
MUNICIPALITIES_ENDPOINT = "https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/Listados/MunicipiosPorProvincia/"
GAS_STATION_ENDPOINT = "https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/FiltroMunicipioProducto/"
# EarthStations/ProductMunicipalityFilter/{GemeenteID}/{ProductID}	KRIJGEN	Service op https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/FiltroMunicipioProducto/{IDMUNICIPIO}/{IDPRODUCTO}
# EarthStations/ProvincieProductFilter/{ProvinceID}/{ProductID} Service op https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/FiltroProvinciaProducto/{IDPROVINCIA}/{IDPRODUCTO}

UPDATE_INTERVAL = 2
CONF_PROVINCE = "province"
CONF_PRODUCT = "product"
CONF_MUNICIPALITY = "municipality"
CONF_STATION = "station"
