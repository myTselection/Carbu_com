from dataclasses import dataclass

import requests

import spain_const


@dataclass
class Province:
    id: str
    name: str


@dataclass
class Municipality:
    id: str
    name: str


@dataclass
class GasStation:
    id: str
    name: str
    address: str
    product_name: str


@dataclass
class Product:
    id: str
    name: str


@dataclass
class GasStationProduct:
    id: str
    name: str


class GasStationApi:

    @staticmethod
    def get_provinces() -> list[Province]:
        session = requests.Session()
        response = session.get(spain_const.PROVINCES_ENDPOINT)
        json = response.json()
        session.close()
        return list(map(lambda p: Province(id=p['IDPovincia'], name=p['Provincia'].title()), json))

    @staticmethod
    def get_municipalities(province_id):
        session = requests.Session()
        response = session.get(spain_const.MUNICIPALITIES_ENDPOINT + province_id)
        json = response.json()
        session.close()
        return list(map(lambda m: Municipality(id=m['IDMunicipio'], name=m['Municipio']), json))

    @staticmethod
    def get_gas_stations(municipality_id, product_id):
        session = requests.Session()
        response = session.get(f"{spain_const.GAS_STATION_ENDPOINT}{municipality_id}/{product_id}")
        json = response.json()
        session.close()
        # product_name = next(filter(lambda p: p.id == product_id, GasStationApi.get_products()), None).id
        # stations = list(map(lambda s:
        #                     GasStation(name=s["Rótulo"].title(),
        #                                address=s["Dirección"].title(),
        #                                id=s["IDEESS"],
        #                                product_name=product_name),
        #                     json['ListaEESSPrecio']))

        # stations.sort(key=lambda x: x.name)
        return json
    
    @staticmethod
    def get_gas_stations_provincia(provincia_id, product_id):
        session = requests.Session()
        response = session.get(f"{spain_const.GAS_STATION_ENDPOINT_PROVINCIA}{provincia_id}/{product_id}")
        json = response.json()
        session.close()
        # product_name = next(filter(lambda p: p.id == product_id, GasStationApi.get_products()), None).id
        # stations = list(map(lambda s:
        #                     GasStation(name=s["Rótulo"].title(),
        #                                address=s["Dirección"].title(),
        #                                id=s["IDEESS"],
        #                                product_name=product_name),
        #                     json['ListaEESSPrecio']))

        # stations.sort(key=lambda x: x.name)
        return json

    @staticmethod
    def get_gas_price(station_id, municipality_id, product_id):
        session = requests.Session()
        response = session.get(f"{spain_const.GAS_STATION_ENDPOINT}{municipality_id}/{product_id}")
        json = response.json()
        session.close()
        gas_station = next(filter(lambda g: g['IDEESS'] == station_id, json['ListaEESSPrecio']), None)
        if gas_station is None:
            return None

        price = gas_station['PrecioProducto'].replace(',', '.')
        try:
            return float(price)
        except ValueError:
            return None

    @staticmethod
    def get_station_name(station_id, municipality_id, product_id):
        session = requests.Session()
        response = session.get(f"{spain_const.GAS_STATION_ENDPOINT}{municipality_id}/{product_id}")
        json = response.json()
        session.close()
        gas_station = next(filter(lambda g: g['IDEESS'] == station_id, json['ListaEESSPrecio']), None)
        if gas_station is None:
            return None

        product = next(filter(lambda x: x.id == product_id, GasStationApi.get_products()), None)
        if product is None:
            return None

        return GasStationProduct(name=f"{product.name}, {gas_station['Rótulo'].title()}", id=f"{product_id}-{station_id}")

    @staticmethod
    def get_products():
        return [
            Product(name="Gasolina 95 E5", id="1"),
            Product(name="Gasolina 98 E5", id="3"),
            Product(name="Gasóleo A", id="4"),
            Product(name="Gasóleo Premium", id="5"),
            Product(name="Gasóleo B", id="6"),
            Product(name="Gasóleo C", id="7"),
            Product(name="Biodiesel", id="8"),
            Product(name="Bioetanol", id="16"),
            Product(name="Gases licuados del petróleo", id="17"),
            Product(name="Gas natural comprimido", id="18"),
            Product(name="Gas natural licuado", id="19"),
            Product(name="Gasolina 95 E5 Premium ", id="20"),
            Product(name="Gasolina 98 E10", id="21"),
            Product(name="Gasolina 95 E10", id="23"),
        ]
