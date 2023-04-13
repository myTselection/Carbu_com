[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/myTselection/carbu_com.svg)](https://github.com/myTselection/carbu_com/releases)
![GitHub repo size](https://img.shields.io/github/repo-size/myTselection/carbu_com.svg)

[![GitHub issues](https://img.shields.io/github/issues/myTselection/carbu_com.svg)](https://github.com/myTselection/carbu_com/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/myTselection/carbu_com.svg)](https://github.com/myTselection/carbu_com/commits/master)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/myTselection/carbu_com.svg)](https://github.com/myTselection/carbu_com/graphs/commit-activity)

# Carbu.com
[Carbu.com](https://www.Carbu.com/) Home Assistant custom component. This custom component has been built from the ground up to bring Carbu.com & Mazout.com site data to compare and save on your fuel oil, diesel and Super prices and integrate this information into Home Assistant to help you towards a better follow up. This integration is built against the public website provided by Carbu.com for Belgium and has not been tested for any other countries.

This integration is in no way affiliated with Carbu.com.

Some discussion on this topic can be found within [the Home Assistant community forum](https://community.home-assistant.io/t/rest-sensor-needs-to-get-latest-element-of-list/404882/4).

For electricity price expectations [this Entso-E HACS integration](https://github.com/JaccoR/hass-entso-e) can be used.

<p align="center"><img src="https://raw.githubusercontent.com/myTselection/carbu_com/master/icon.png"/></p>


## Installation
- [HACS](https://hacs.xyz/): add url https://github.com/myTselection/carbu_com as custom repository (HACS > Integration > option: Custom Repositories)
- Restart Home Assistant
- Add 'Carbu.com' integration via HA Settings > 'Devices and Services' > 'Integrations'
- Provide country (currently only tested with BE), postal code and select the desired sensors
   - If your postal code is not unique, the name of the town can be added. If provided, it will be used to find the matching location. See [carbu.com](https://carbu.com) website for known towns and postal codes.

## Integration
- <details><summary>Sensor diesel and super <code>sensor.carbu_com_[fueltype]_[postalcode]_price</code> and fuel oil <code>sensor.carbu_com_[fueltype]_[postalcode]_[quantity]l_price</code></summary>

    | Attribute | Description |
    | --------- | ----------- |
    | State     | **Price** |
    | `last update `   | Timestamp info last retrieved from the carbu.com website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
    | `fueltype`   | Fuel type |
    | `fuelname` | Full name of the fuel type |
    | `postalcode`  | Postalcode at which the price was retrieved |
    | **`supplier`**  | **Name of the supplier of the fuel** |
    | `url`  | Url with details of the supplier |
    | `logourl`  | Url with the logo of the supplier |
    | `address`  | Address of the supplier |
    | `city`  | City of the supplier |
    | `lat`  | Latitude of the supplier |
    | `lon`  | Longitude of the supplier |
    | **`distance`**  | **Distance to the supplier vs postal code** |
    | `date`  | Date for the validity of the price |
    | `quantity`  | Quantity of fuel (only for fuel oil) |
    | `score`  | Score of the supplier |
    | `suppliers`  | Full json list of all suppliers with prices and detials found in neighbourhood around the postal code |
    
    </details>
    
- <details><summary>Sensor diesel and super price in neighbourhood: <code>sensor.carbu_com_[fueltype]_[postalcode]_[*]km</code> for 5km and 10km</summary>

    | Attribute | Description |
    | --------- | ----------- |
    | State     | Price |
    | `last update `   | Timestamp info last retrieved from the carbu.com website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
    | `fueltype`   | Fuel type |
    | `fuelname` | Full name of the fuel type |
    | `postalcode`  | Postalcode at which the price was retrieved |
    | `supplier`  | Name of the supplier of the fuel |
    | `url`  | Url with details of the supplier |
    | `logourl`  | Url with the logo of the supplier |
    | `address`  | Address of the supplier |
    | `city`  | City of the supplier |
    | `lat`  | Latitude of the supplier |
    | `lon`  | Longitude of the supplier |
    | `region`  | Distand 5km or 10km around postal code in which cheapest prices is found |
    | **`distance`**  | **Distance to the supplier vs postal code** |
    | **`price diff`**  | **Price difference between the cheapest found in region versus the local price** |
    | `price diff %`  | Price difference in % between the cheapest found in region versus the local price |
    | `price diff 30l`  | Price difference for 30 liters between the cheapest found in region versus the local price |
    | `date`  | Date for the validity of the price |
    | `quantity`  | Quantity of fuel (only for fuel oil) |
    | `score`  | Score of the supplier |
    </details>
    
- <details><summary>Sensor diesel and super prediction: <code>sensor.carbu_com_[fueltype]_prediction</code></summary>
    
    | Attribute | Description |
    | --------- | ----------- |
    | State     | Price |
    | `last update` | Timestamp info last retrieved from the carbu.com website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
    | `fueltype`   | Fuel type |
    | **`trend`** | **Percentage of increase or decrease predicted for coming days** |
    | `date`  | Date for the validity of the price |
    </details>
    
- <details><summary>Sensor fuel oil prediction: <code>sensor.carbu_com_[oiltype]_[quantity]l_prediction</code></summary>

    | Attribute | Description |
    | --------- | ----------- |
    | State     | Price |
    | `last update `   | Timestamp info last retrieved from the carbu.com website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
    | `fueltype`   | Fuel type |
    | `fuelname` | Full name of the fuel type |
    | **`trend`** | **Percentage of increase or decrease predicted for coming days** |
    | `price` | Predicted maximum price for type and quantity |
    | `date`  | Date for the validity of the price |
    | `quantity`  | Quantity for which the price is expected. Main difference between below or above 2000l |
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
          src="{{state_attr('sensor.carbu_com_diesel_1000_price','logourl')}}"
          width="40"/>
          [{{state_attr('sensor.carbu_com_diesel_1000_5km','supplier')}}]({{state_attr('sensor.carbu_com_diesel_1000_5km','url')}})

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
          src="{{state_attr('sensor.carbu_com_super95_3010_price','logourl')}}"
          width="45"/> </center>


          <center>


          [{{state_attr('sensor.carbu_com_super95_3010_price','supplier')}}]({{state_attr('sensor.carbu_com_super95_3010_5km','url')}})

          ### <center>{{states('sensor.carbu_com_super95_3010_price')}} €/l
      - type: markdown
        content: >
          #### <center>5 km</center>

          <center><img
          src="{{state_attr('sensor.carbu_com_super95_3010_5km','logourl')}}"
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
          src="{{state_attr('sensor.carbu_com_super95_3010_10km','logourl')}}"
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
