[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/default)
[![GitHub release](https://img.shields.io/github/release/myTselection/carbu_com.svg)](https://github.com/myTselection/carbu_com/releases)
![GitHub repo size](https://img.shields.io/github/repo-size/myTselection/carbu_com.svg)

[![GitHub issues](https://img.shields.io/github/issues/myTselection/carbu_com.svg)](https://github.com/myTselection/carbu_com/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/myTselection/carbu_com.svg)](https://github.com/myTselection/carbu_com/commits/master)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/myTselection/carbu_com.svg)](https://github.com/myTselection/carbu_com/graphs/commit-activity)

# Carbu.com Home Assistant integration
[Carbu.com](https://www.Carbu.com/) Home Assistant custom component. This custom component has been built from the ground up to bring Carbu.com & Mazout.com site data to compare and save on your fuel oil, diesel, lpg and Super prices and integrate this information into Home Assistant to help you towards a better follow up. This integration is built against the public website provided by Carbu.com and other similar sites. Sensors will be created for the currently **cheapest** gas station in a region (at location, within 5km and within 10km).

This integration is in no way affiliated with Carbu.com. 

| :warning: Please don't report issues with this integration to Carbu or other platforms, they will not be able to support you.** |
| --------------------------------------------------------------------------------------------------------------------------------|

Since R5.0, beta support for fuel prices in Germany (DE) has been added. City or postalcode can be provided as location.

Since R6.0, beta support for fuel prices in Italy (IT) has been added. Postalcode and town need to be provided.

Since R7.0, beta support for fuel prices in Netherlands (NL) has been added. Postalcode and town need to be provided.

Since R8.0, beta support for fuel prices in Spain (ES) has been added. Postalcode and town need to be provided.


Some discussion on this topic can be found within [the Home Assistant community forum](https://community.home-assistant.io/t/rest-sensor-needs-to-get-latest-element-of-list/404882/4).

For electricity price expectations [this Entso-E HACS integration](https://github.com/JaccoR/hass-entso-e) can be used.

For cheapest Belgian gas and electricity contracts, prices and promotions, please check out my other integration [MyEnergy](https://github.com/myTselection/MyEnergy)

<p align="center"><img src="https://raw.githubusercontent.com/myTselection/carbu_com/master/icon.png"/></p>


## Installation
- [HACS](https://hacs.xyz/): add url https://github.com/myTselection/carbu_com as custom repository (HACS > Integration > option: Custom Repositories)
   -    [![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=myTselection&repository=Carbu_com&category=integration)
- Restart Home Assistant
- Add 'Carbu.com' integration via HA Settings > 'Devices and Services' > 'Integrations'
- Provide country, postal code and select the desired sensors
   - The name of the town can be selected from the dropdown in the next step of the setup config flow. See [carbu.com](https://carbu.com) website for known towns and postal codes. (Only for BE/FR/LU)
   - An extra checkbox can be set to select a specific individual gas station. If set, a station can be selected in a dropdown with known gas stations (for which a price is available) close to the provided postalcode and town. No sensor for 5km and 10km will be created, only the price sensor for the individual selected station. The name of the sensor will contain the name of the supplier.
   - For Italy & Netherlands, the town will be requested in the second step of the config flow
- A filter on supplier brand name can be set (optional). If the filter match, the fuel station will be considered, else next will be searched. A python regex filter value be set
- An option is avaible to show a logo (entity picture) with price or the original logo provided by the source. This is mainly visible when mapping the sensor on a map.
- After setting up the integration, the configuration can be updated using the 'Configure' button of the integration. The usage of a station filter can be enabled and set, the usage of a template to set the 'friendly name' of each sensor type can be enabled and set and the usage of icons with price indication can be enabled or disabled.
  - The checkboxes are required since else clearing the text of the configuration was not recorded (HA bug?) and filter or templates could no longer be removed once set.
  - When setting a sensor 'friendly name' template, any sensor attribute can be used as a placeholder which will be replaced with the actual value. Eg: `Price {fueltype} {fuelname} {supplier}` could be used as a template for te Price sensor. All available attributes can be fetched using the 'Developer Tools' > 'States' > 'Attributes' view in HA or using the tables listed below.

## Integration
### Sensors
- <details><summary>Sensor with lowest diesel and super <code>sensor.carbu_com_[fueltype]_[postalcode]_price</code> and lowest fuel oil <code>sensor.carbu_com_[fueltype]_[postalcode]_[quantity]l_price</code> Fuel oil only supported for BE/FR/LU</summary>

    | Attribute | Description |
    | --------- | ----------- |
    | State     | **Price** |
    | `last update `   | Timestamp info last retrieved from the carbu.com website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
    | `fueltype`   | Fuel type |
    | `fuelname` | Full name of the fuel type |
    | `postalcode`  | Postalcode at which the price was retrieved |
    | **`supplier`**  | **Name of the supplier of the fuel** |
    | `supplier_brand`  | Brand name of the supplier (eg Shell, Texaco, ...) Not supported for DE |
    | `url`  | Url with details of the supplier |
    | `entity_picture`  | Url with the logo of the supplier |
    | `address`  | Address of the supplier |
    | `city`  | City of the supplier |
    | `latitude`  | Latitude of the supplier |
    | `longitude`  | Longitude of the supplier |
    | **`distance`**  | **Distance to the supplier vs postal code** ( Not supported for IT ) |
    | `date`  | Date for the validity of the price |
    | `quantity`  | Quantity of fuel (only for fuel oil) |
    | `score`  | Score of the supplier |
    | `id`  | Unique id of the supplier |
    | ~~`suppliers`~~  | ~~Full json list of all suppliers with prices and detials found in neighbourhood around the postal code~~ |
    
    </details>
    
- <details><summary>Sensor with lowest diesel and super price in neighbourhood: <code>sensor.carbu_com_[fueltype]_[postalcode]_[*]km</code> for 5km and 10km </summary>

    | Attribute | Description |
    | --------- | ----------- |
    | State     | Price |
    | `last update `   | Timestamp info last retrieved from the carbu.com website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
    | `fueltype`   | Fuel type |
    | `fuelname` | Full name of the fuel type |
    | `postalcode`  | Postalcode at which the price was retrieved |
    | `supplier`  | Name of the supplier of the fuel |
    | `supplier_brand`  | Brand name of the supplier (eg Shell, Texaco, ...) Not supported for DE |
    | `url`  | Url with details of the supplier |
    | `entity_picture`  | Url with the logo of the supplier |
    | `address`  | Address of the supplier |
    | `city`  | City of the supplier |
    | `latitude`  | Latitude of the supplier Not supported for DE |
    | `longitude`  | Longitude of the supplier Not supported for DE |
    | `region`  | Distand 5km or 10km around postal code in which cheapest prices is found |
    | **`distance`**  | **Distance to the supplier vs postal code** ( Not supported for IT )|
    | **`price diff`**  | **Price difference between the cheapest found in region versus the local price** |
    | `price diff %`  | Price difference in % between the cheapest found in region versus the local price |
    | `price diff 30l`  | Price difference for 30 liters between the cheapest found in region versus the local price |
    | `date`  | Date for the validity of the price |
    | `quantity`  | Quantity of fuel (only for fuel oil) |
    | `score`  | Score of the supplier |
    | `id`  | Unique id of the supplier |
    </details>

- <details><summary>Sensor with official diesel and super price <code>sensor.carbu_com_[fueltype]_officia_[fueltypecode]</code>, only supported for BE/FR/LU</summary>

    | Attribute | Description |
    | --------- | ----------- |
    | State     | **Price** |
    | `last update `   | Timestamp info last retrieved from the carbu.com website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
    | `fueltype`   | Fuel type |
    | `price`   | Price |
    | `date`  | Date for the validity of the price |
    | `price next`   | Next official price |
    | `date next`  | Date as of when the next price will be applicable |
    </details>
    
- <details><summary>Sensor diesel and super prediction: <code>sensor.carbu_com_[fueltype]_prediction</code> Only supported for BE/FR/LU</summary>
    
    | Attribute | Description |
    | --------- | ----------- |
    | State     | Percentage of increase or decrease predicted for coming days |
    | `last update` | Timestamp info last retrieved from the carbu.com website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
    | `fueltype`   | Fuel type |
    | **`trend`** | **Percentage of increase or decrease predicted for coming days** |
    | `date`  | Date for the validity of the price |
    </details>
    
- <details><summary>Sensor fuel oil prediction: <code>sensor.carbu_com_[oiltype]_[quantity]l_prediction</code> Only supported for BE/FR/LU</summary>

    | Attribute | Description |
    | --------- | ----------- |
    | State     | Percentage of increase or decrease predicted for coming days |
    | `last update `   | Timestamp info last retrieved from the carbu.com website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
    | `fueltype`   | Fuel type |
    | `fuelname` | Full name of the fuel type |
    | **`trend`** | **Percentage of increase or decrease predicted for coming days** |
    | `price` | Predicted maximum price for type and quantity |
    | `date`  | Date for the validity of the price |
    | `current official max price`  | Currently official max price |
    | `current official max price date`  | Date of the currently official max price |
    | `quantity`  | Quantity for which the price is expected. Main difference between below or above 2000l |
    </details>

### Services
A **service `carbu_com.get_lowest_fuel_price`** to get the lowest fuel price in the area of a postalcode is available. For a given fuel type and a distance in km, the lowest fuel price will be fetched and an event will be triggered with all the details found. Similar, the service **`carbu_com.get_lowest_fuel_price_coor`** can be called providing latitude and longitude coordinates instead of country, postalcode and town.

- <details><summary>Event data returned, event name: <code>carbu_com_lowest_fuel_price</code> /  <code>carbu_com_lowest_fuel_price_coor</code></summary>

    | Attribute | Description |
    | --------- | ----------- |
    | `fueltype`   | Fuel type |
    | `fuelname` | Full name of the fuel type |
    | `postalcode`  | Postalcode at which the price was retrieved |
    | `supplier`  | Name of the supplier of the fuel |
    | `supplier_brand`  | Brand name of the supplier (eg Shell, Texaco, ...) Not supported for DE |
    | `url`  | Url with details of the supplier |
    | `entity_picture`  | Url with the logo of the supplier |
    | `address`  | Address of the supplier |
    | `city`  | City of the supplier |
    | `latitude`  | Latitude of the supplier Not supported for DE |
    | `longitude`  | Longitude of the supplier Not supported for DE |
    | `region`  | Distand 5km or 10km around postal code in which cheapest prices is found |
    | **`distance`**  | **Distance to the supplier vs postal code** ( Not supported for IT ) |
    | **`price diff`**  | **Price difference between the cheapest found in region versus the local price** |
    | `price diff %`  | Price difference in % between the cheapest found in region versus the local price |
    | `price diff 30l`  | Price difference for 30 liters between the cheapest found in region versus the local price |
    | `date`  | Date for the validity of the price |
    </details>

- <details><summary>Example service call using iphone gecoded user location</summary>

   ```
   service: carbu_com.get_lowest_fuel_price
   data:
     fuel_type: diesel
     country: BE
     postalcode: "{{state_attr('sensor.iphone_geocoded_location','Postal Code')}}"
     town: "{{state_attr('sensor.iphone_geocoded_location','Locality')}}"
     max_distance: 5
     filter: Total

   ```

    </details>

- <details><summary>Example service call using iphone lat lon coordinates location</summary>

   ```
   service: carbu_com.get_lowest_fuel_price_coor
   data:
     fuel_type: diesel
     latitude: "{{state_attr('device_tracker.iphone','latitude')}}"
     longitude: "{{state_attr('device_tracker.iphone','longitude')}}"
     max_distance: 5
     filter: Total

   ```

    </details>
    
- <details><summary>Example automation triggered by event</summary>

   ```
   alias: Carbu event
   description: ""
   trigger:
     - platform: event
       event_type: carbu_com_lowest_fuel_price # or carbu_com_lowest_fuel_price_coor
   condition: []
   action:
     - service: notify.persistent_notification
       data:
         message: >-
           {{ trigger.event.data.supplier_brand }}: {{ trigger.event.data.price }}€
           at {{ trigger.event.data.distance }}km, {{ trigger.event.data.address }}
   mode: single

   ```

    </details>
    
    
A **service `carbu_com.get_lowest_fuel_price_on_route`** (**BETA**) to get the lowest fuel price on the route in between two postal codes. Can be used for example to get the lowest price between your current location and your home, or between office and home etc. The lowest fuel price will be fetched and an event will be triggered with all the details found. The route is retrieved using [Open Source Routing Machine](https://project-osrm.org/). For performance and request limitations, 30% of the locations (evenly distributed) are used for which the best price of each on a distance of 3km is fetched. So no guarantee this would be the absolute best price. If too long routes are searched, it might get stuck because of the limitations of the quota of the free API. Similar, the service **`carbu_com.get_lowest_fuel_price_on_route_coor`** can be called providing latitude and longitude coordinates instead of country, postalcode and town.

- <details><summary>Event data returned, Event name: <code>carbu_com_lowest_fuel_price_on_route</code> or <code>carbu_com_lowest_fuel_price_on_route_coor</code></summary>

    | Attribute | Description |
    | --------- | ----------- |
    | `fueltype`   | Fuel type |
    | `fuelname` | Full name of the fuel type |
    | `postalcode`  | Postalcode at which the price was retrieved |
    | `supplier`  | Name of the supplier of the fuel |
    | `supplier_brand`  | Brand name of the supplier (eg Shell, Texaco, ...) Not supported for DE |
    | `url`  | Url with details of the supplier |
    | `entity_picture`  | Url with the logo of the supplier |
    | `address`  | Address of the supplier |
    | `city`  | City of the supplier |
    | `latitude`  | Latitude of the supplier Not supported for DE |
    | `longitude`  | Longitude of the supplier Not supported for DE |
    | `region`  | Distand 5km or 10km around postal code in which cheapest prices is found |
    | **`distance`**  | **Distance to the supplier vs postal code** ( Not supported for IT ) |
    | **`price diff`**  | **Price difference between the cheapest found in region versus the local price** ( Not supported for IT ) |
    | `price diff %`  | Price difference in % between the cheapest found in region versus the local price ( Not supported for IT ) |
    | `price diff 30l`  | Price difference for 30 liters between the cheapest found in region versus the local price |
    | `date`  | Date for the validity of the price |
    </details>

- <details><summary>Example service call</summary>

   ```
   service: carbu_com.get_lowest_fuel_price_on_route
   data:
     fuel_type: diesel
     country: BE
     from_postalcode: 3620 #"{{state_attr('sensor.iphone_geocoded_location','Postal Code')}}"
     to_postalcode: 3660

   ```

    </details>

- <details><summary>Example service call using lat lon coordinates location</summary>

   ```
   service: carbu_com.get_lowest_fuel_price_on_route
   data:
     fuel_type: diesel
     from_latitude: 50.8503
     from_longitude: 4.3517
     to_latitude: 51.2194
     to_longitude: 4.4025

   ```

    </details>
    
- <details><summary>Example automation triggered by event</summary>

   ```
   alias: Carbu event
   description: ""
   trigger:
     - platform: event
       event_type: carbu_com_lowest_fuel_price_on_route # or carbu_com_lowest_fuel_price_on_route_coor
   condition: []
   action:
     - service: notify.persistent_notification
       data:
         message: >-
           {{ trigger.event.data.supplier_brand }}: {{ trigger.event.data.price }}€
           at {{ trigger.event.data.distance }}km, {{ trigger.event.data.address }}
   mode: single

   ```

    </details>
    

## Status
Still some optimisations are planned, see [Issues](https://github.com/myTselection/carbu_com/issues) section in GitHub.

## Technical pointers
The main logic and API connection related code can be found within source code Carbu.com/custom_components/Carbu.com:
- [sensor.py](https://github.com/myTselection/carbu_com/blob/master/custom_components/carbu_com/sensor.py)
- [utils.py](https://github.com/myTselection/carbu_com/blob/master/custom_components/carbu_com/utils.py) -> mainly ComponentSession class

All other files just contain boilerplat code for the integration to work wtihin HA or to have some constants/strings/translations.

If you would encounter some issues with this custom component, you can enable extra debug logging by adding below into your `configuration.yaml`:
```
logger:
  default: info
  logs:
     custom_components.carbu_com: debug
```

## Example usage:
### Gauge & Markdown
<p align="center"><img src="https://raw.githubusercontent.com/myTselection/carbu_com/master/Markdown%20Gauge%20Card%20example.png"/></p>
<details><summary>Click to show Mardown code example</summary>

```
type: vertical-stack
cards:
  - type: horizontal-stack
    cards:
      - type: markdown
        content: >
          ## Diesel

          <img
          src="{{state_attr('sensor.carbu_com_diesel_1000_5km','entity_picture')}}"
          width="40"/>
          [{{state_attr('sensor.carbu_com_diesel_1000_5km','supplier')}}]({{state_attr('sensor.carbu_com_diesel_1000_5km','url')}} "{{state_attr('sensor.carbu_com_diesel_1000_5km','address')}}")

          #### Coming days: {% if
          states('sensor.carbu_com_diesel_prediction')|float < 0 %}<font
          color=green>{{states('sensor.carbu_com_diesel_prediction')}}%</font>{%
          else %}<font
          color=red>{{states('sensor.carbu_com_diesel_prediction')}}%</font>{%
          endif %}

          Best price in region (10km vs local):
          {{states('sensor.carbu_com_diesel_1000_10km')}},
          {{state_attr('sensor.carbu_com_diesel_1000_10km','supplier')}}
          {{state_attr('sensor.carbu_com_diesel_1000_10km','price diff %')}}
          ({{state_attr('sensor.carbu_com_diesel_1000_10km','price diff 30l')}}
          on 30l)

          Best price in region (10km vs 5km):
          {{states('sensor.carbu_com_diesel_1000_10km')}}€/l:
          {{state_attr('sensor.carbu_com_diesel_1000_10km','supplier')}}
          {{(states('sensor.carbu_com_diesel_1000_5km')|float -
          states('sensor.carbu_com_diesel_1000_10km')|float)|round(2)}}€
          ({{(states('sensor.carbu_com_diesel_1000_5km')|float -
          states('sensor.carbu_com_diesel_1000_10km')|float)|round(2)*30}}€ on
          30l)
      - type: markdown
        content: >-
          ## Mazout

          [{{state_attr('sensor.carbu_com_oilstd_1000_1000l_price','supplier')}}]({{state_attr('sensor.carbu_com_oilstd_1000_1000l_price','url')}})


          #### Coming days: {% if
          states('sensor.carbu_com_oilextra_1000l_prediction')|float < 0 %}<font
          color=green>{{states('sensor.carbu_com_oilextra_1000l_prediction')}}%</font>{%
          else %}<font
          color=red>{{states('sensor.carbu_com_oilextra_1000l_prediction')}}%</font>{%
          endif %}
  - type: horizontal-stack
    cards:
      - type: gauge
        entity: sensor.carbu_com_diesel_1000_5km
        min: 0
        max: 5
        needle: true
        unit: €/l
        name: Diesel prijs
        severity:
          green: 0
          yellow: 0.8
          red: 2
      - type: gauge
        entity: sensor.carbu_com_oilstd_1000_1000l_price
        min: 0
        max: 5
        needle: true
        unit: €/l
        name: Mazout prijs
        severity:
          green: 0
          yellow: 0.8
          red: 2
  - type: history-graph
    entities:
      - entity: sensor.carbu_com_diesel_1000_5km
        name: Diesel
      - entity: sensor.carbu_com_oilextra_1000_1000l_price
        name: Oil extra (per 1000l)
    hours_to_show: 500
    refresh_interval: 60
    
```
</details>


### Markdown example card with prices for local, 5 & 10 km (by @bavala3010)
<p align="center"><img src="https://raw.githubusercontent.com/myTselection/carbu_com/master/Markdown%20Gauge%20Card%20example2.png"/></p>
<details><summary>Click to show Mardown code example</summary>

```
type: vertical-stack
cards:
  - type: markdown
    content: >
      ## Super95 benzine

      #### Komende dagen: {% if
      states('sensor.carbu_com_super95_prediction')|float < 0 %}<font
      color=green>{{states('sensor.carbu_com_super95_prediction')}}%</font>{%
      else %}<font
      color=red>{{states('sensor.carbu_com_super95_prediction')}}%</font>{%
      endif %}
  - type: horizontal-stack
    cards:
      - type: markdown
        content: >
          #### <center>lokaal </center>


          <center><img
          src="{{state_attr('sensor.carbu_com_super95_3010_price','entity_picture')}}"
          width="45"/> </center>


          <center>


          [{{state_attr('sensor.carbu_com_super95_3010_price','supplier')}}]({{state_attr('sensor.carbu_com_super95_3010_5km','url')}})

          ### <center>{{states('sensor.carbu_com_super95_3010_price')}} €/l
      - type: markdown
        content: >
          #### <center>5 km</center>

          <center><img
          src="{{state_attr('sensor.carbu_com_super95_3010_5km','entity_picture')}}"
          width="45"/></center>


          <center>


          [{{state_attr('sensor.carbu_com_super95_3010_5km','supplier')}}]({{state_attr('sensor.carbu_com_super95_3010_5km','url')}})

          ### <center>{{states('sensor.carbu_com_super95_3010_5km')}} €/l

          Besparing tov lokaal =
          {{state_attr('sensor.carbu_com_super95_3010_5km','price diff %')}} of
          **{{state_attr('sensor.carbu_com_super95_3010_5km','price diff
          30l')}}** op 30l
      - type: markdown
        content: >
          #### <center>10 km

          <center><img
          src="{{state_attr('sensor.carbu_com_super95_3010_10km','entity_picture')}}"
          width="45"/></center>


          <center>


          [{{state_attr('sensor.carbu_com_super95_3010_10km','supplier')}}]({{state_attr('sensor.carbu_com_super95_3010_5km','url')}})

          ### <center>{{states('sensor.carbu_com_super95_3010_10km')}} €/l

          Besparing tov lokaal =
          {{state_attr('sensor.carbu_com_super95_3010_10km','price diff %')}} of
          **{{state_attr('sensor.carbu_com_super95_3010_10km','price diff
          30l')}}** op 30l


```
</details>



### Markdown example card on map
The sensors contain latitude and longitude attributes and entity_picture attributes to allow the sensors to be shown nicely on a map
<p align="center"><img src="https://raw.githubusercontent.com/myTselection/carbu_com/master/Markdown%20Map%20Card%20example.png"/></p>
<details><summary>Click to show Mardown code example</summary>

```
type: map
entities:
  - entity: sensor.carbu_com_diesel_1000_price
  - entity: sensor.carbu_com_diesel_1000_5km
  - entity: sensor.carbu_com_diesel_1000_10km
title: carbu
```
</details>
