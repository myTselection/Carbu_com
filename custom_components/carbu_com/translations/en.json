{
    "config": {
        "title": "Carbu.com",
        "step": {
            "user": {
                "description": "Setup Carbu.com and Mazout.com sensors.",
                "data": {
                    "country": "Country (BE/FR/LU/DE)",
                    "postalcode": "Postal code",
                    "town": "Town",
                    "filter": "Supplier brand filter (optional)",
					"super95": "Super 95 (E10)",
					"super98": "Super 98 (E5)",
					"diesel": "Diesel (B7)",
					"oilstd": "Mazout Heating Oil standard (50S)",
					"oilextra": "Mazout Heating Oil extra",
					"quantity": "Mazout Heating Oil quanitity (liters)"
                }
            },
            "town": {
                "data": {
                    "town": "Town"
                }
            },
            "edit": {
                "description": "Setup Carbu.com and Mazout.com sensors.",
                "data": {
                    "country": "Country (BE/FR/LU/DE)",
                    "postalcode": "Postal code",
                    "town": "Town",
                    "filter": "Supplier brand filter (optional)",
					"super95": "Super 95 (E10)",
					"super98": "Super 98 (E5)",
					"diesel": "Diesel (B7)",
					"oilstd": "Mazout Heating Oil standard (50S)",
					"oilextra": "Mazout Heating Oil extra",
					"quantity": "Mazout Heating Oil quanitity (liters)"
                }
            }

        },
        "error": {
            "missing country": "Please provide a valid country: BE/FR/LU/DE",
            "missing postal code": "Please provide a valid postal code",
            "missing data options handler": "Option handler failed",
            "no_valid_settings": "No valid settings check in ha config."
        }
    },
    "options": {
        "step": {
            "edit": {
                "description": "Setup Carbu.com and Mazout.com sensors.",
                "data": {
                    "country": "Country (BE/FR/LU/DE)",
                    "postalcode": "Postal code",
                    "town": "Town",
                    "filter": "Supplier brand filter (optional)",
					"super95": "Super 95 (E10)",
					"super98": "Super 98 (E5)",
					"diesel": "Diesel (B7)",
					"oilstd": "Mazout Heating Oil standard (50S)",
					"oilextra": "Mazout Heating Oil extra",
					"quantity": "Mazout Heating Oil quanitity (liters)"
                }
            }
        },
        "error": {
            "missing country": "Please provide a valid country: BE/FR/LU/DE",
            "missing postal code": "Please provide a valid postal code",
            "missing data options handler": "Option handler failed",
            "no_valid_settings": "No valid settings check in ha config."
        }
    },
    "services": {
        "get_lowest_fuel_price": {
            "name": "get_lowest_fuel_price",
            "description": "Get the lowest fuel price in the neighbourhood of a specific location defined by postalcode and town (optional).",
            "fields": {
                "fuel_type": {
                    "name": "fuel_type",
                    "description": "The type of fuel to look for, supported options: super95, super98 or diesel"
                },
                "country": {
                    "name": "country",
                    "description": "The country to look for, supported options: BE / FR / LU / DE"
                },
                "postalcode": {
                    "name": "postalcode",
                    "description": "The postalcode to look for"
                },
                "town": {
                    "name": "town",
                    "description": "(Optonal) The town to look for"
                },
                "max_distance": {
                    "name": "max_distance",
                    "description": "Max distance in km around postal code to look for lowest fuel price, eg search 5km around postal code"
                },
                "filter": {
                    "name": "filter",
                    "description": "(Optional) Filter out only specific supplier brands, leave empty if any supplier brand is allowed"
                }
            }
        },
        "get_lowest_fuel_price_coor": {
            "name": "get_lowest_fuel_price_coor",
            "description": "Get the lowest fuel price in the neighbourhood of a specific location defined by coordinates latitude and longitude.",
            "fields": {
                "fuel_type": {
                    "name": "fuel_type",
                    "description": "The type of fuel to look for, supported options: super95, super98 or diesel"
                },
                "latitude": {
                    "name": "latitude",
                    "description": "The latitude of the location (N)"
                },
                "longitude": {
                    "name": "longitude",
                    "description": "The longitude of the location (E)"
                },
                "max_distance": {
                    "name": "max_distance",
                    "description": "Max distance in km around postal code to look for lowest fuel price, eg search 5km around postal code"
                },
                "filter": {
                    "name": "filter",
                    "description": "(Optional) Filter out only specific supplier brands, leave empty if any supplier brand is allowed"
                }
            }
        },
        "get_lowest_fuel_price_on_route": {
            "name": "get_lowest_fuel_price_on_route",
            "description": "Get the lowest fuel price on a route between 2 locations defined by postalcodes",
            "fields": {
                "fuel_type": {
                    "name": "fuel_type",
                    "description": "The type of fuel to look for, supported options: super95, super98 or diesel"
                },
                "country": {
                    "name": "country",
                    "description": "The country to look for, supported options: BE / FR / LU / DE"
                },
                "from_postalcode": {
                    "name": "from_postalcode",
                    "description": "The postalcode to look for as start of the route"
                },
                "to_postalcode": {
                    "name": "to_postalcode",
                    "description": "The postalcode to look for as end of the route"
                },
                "to_country": {
                    "name": "to_country",
                    "description": "(Optional) The country of target location to look for, supported options: BE / FR / LU / DE, if no to_country is provided, country will be used same for source and target location"
                },
                "filter": {
                    "name": "filter",
                    "description": "(Optional) Filter out only specific supplier brands, leave empty if any supplier brand is allowed"
                }
            }
        },
        "get_lowest_fuel_price_on_route_coor": {
            "name": "get_lowest_fuel_price_on_route_coor",
            "description": "Get the lowest fuel price on a route between 2 locations  defined by coordinates latitude and longitude.",
            "fields": {
                "fuel_type": {
                    "name": "fuel_type",
                    "description": "The type of fuel to look for, supported options: super95, super98 or diesel"
                },
                "from_latitude": {
                    "name": "from_latitude",
                    "description": "The latitude of the source location (N)"
                },
                "from_longitude": {
                    "name": "from_longitude",
                    "description": "The longitude of the source location (E)"
                },
                "to_latitude": {
                    "name": "to_latitude",
                    "description": "The latitude of the target location (N)"
                },
                "to_longitude": {
                    "name": "to_longitude",
                    "description": "The longitude of the target location (E)"
                },
                "filter": {
                    "name": "filter",
                    "description": "(Optional) Filter out only specific supplier brands, leave empty if any supplier brand is allowed"
                }
            }
        }
    }
}