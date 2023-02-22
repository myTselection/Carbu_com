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

<p align="center"><img src="https://raw.githubusercontent.com/myTselection/carbu_com/master/icon.png"/></p>


## Installation (ALPHA VERSION, NOT READY FOR USAGE!!!!)
- [HACS](https://hacs.xyz/): add url https://github.com/myTselection/carbu_com as custom repository (HACS > Integration > option: Custom Repositories)
- Restart Home Assistant
- Add 'Carbu.com' integration via HA Settings > 'Devices and Services' > 'Integrations'
- Provide Carbu.com username and password

## Integration
- <details><summary>Sensor <code>sensor.carbu_com_<phonenr>_voice_sms</code></summary>

    | Attribute | Description |
    | --------- | ----------- |
    | State     | Percentage of used call and sms based on total volume and used amount |
    | `last update `   | Timestamp info last retrieved from the youfone website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
    | `phone_number`   | Phone number of the sim card |
    | `used_percentage` | Percentage of used call and sms based on total volume and used amount |
    | `period_used_percentage`  | Percentage of period that has passed. Usage will be reset once period has fully passed. |
    | `total_volume`  | Total volume of available call & sms within subscription |
    | `includedvolume_usage`  | Used amout of call & sms |
    | `unlimited`  | Indication if it's an unlimited subscription (not tested) |
    | `period_start`  | Start date of the next period |
    | `period_days_left`  | Number of days left in current period |
    | `extra_costs`  | Amount of extra costs (eg when usage above volume within subscription) |
    | `usage_details_json`  | Json with full details of usage as received from youfone website |
    </details>
  
- <details><summary>Sensor <code>sensor.carbu_com_<phonenr>_internet</code></summary>

    | Attribute | Description |
    | --------- | ----------- |
    | State     | Percentage of used data based on total volume and used amount |
    | `last update `   | Timestamp info last retrieved from the youfone website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
    | `phone_number`   | Phone number of the sim card |
    | `used_percentage` | Percentage of used data based on total volume and used amount |
    | `period_used_percentage`  | Percentage of period that has passed. Usage will be reset once period has fully passed. |
    | `total_volume`  | Total volume of available data within subscription |
    | `includedvolume_usage`  | Used amout of data |
    | `unlimited`  | Indication if it's an unlimited subscription (not tested) |
    | `period_start`  | Start date of the next period |
    | `period_days_left`  | Number of days left in current period |
    | `extra_costs`  | Amount of extra costs (eg when usage above volume within subscription) |
    | `usage_details_json`  | Json with full details of usage as received from youfone website | 
    </details>
    
- <details><summary>Sensor <code>sensor.carbu_com_<phonenr>_subscription_info</code></summary>

    | Attribute | Description |
    | --------- | ----------- |
    | State     | Info related to the Youfone subscription |
    | `last update `   | Timestamp info last retrieved from the youfone website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
    | `SubscriptionType`   | Info related to the Youfone subscription |
    | `Price` | Subscription monthly rate |
    | `ContractStartDate`  | Contract Start Date. |
    | `ContractDuration`  | Contract duration |
    | `Msisdn`  | SIM unique phone number |
    | `PUK`  | PUK code of the sim card |
    | `ICCShort`  | SIM card unique id |
    | `MsisdnStatus`  | Status of the SIM card |
    | `DataSubscription`  | Details (volume indication) of the data subscription |
    | `VoiceSmsSubscription`  | Details (volume indication) of the call & sms subscription |
    </details>

## Status
Still some optimisations are planned, see [Issues](https://github.com/myTselection/carbu_com/issues) section in GitHub.

## Technical pointers
The main logic and API connection related code can be found within source code Carbu.com/custom_components/Carbu.com:
- [sensor.py](https://github.com/myTselection/carbu_com/blob/master/custom_components/carbu_com/sensor.py)
- [utils.py](https://github.com/myTselection/carbu_com/blob/master/custom_components/carbu_com/utils.py) -> mainly ComponentSession class

All other files just contain boilerplat code for the integration to work wtihin HA or to have some constants/strings/translations.

## Example usage: (using [dual gauge card](https://github.com/custom-cards/dual-gauge-card))
### Gauge & Markdown
<p align="center"><img src="https://raw.githubusercontent.com/myTselection/carbu_com/master/Markdown%20Gauge%20Card%20example.png"/></p>
<details><summary>Click to show Mardown code example</summary>

```
type: vertical-stack
cards:
  - type: markdown
    content: >-
      ## <img
      src="https://raw.githubusercontent.com/myTselection/carbu_com/master/icon.png"
      width="30"/>&nbsp;&nbsp;Youfone
      {{state_attr('sensor.carbu_com_<phonenr>_voice_sms','phone_number')}}


      ### Totaal bel/sms verbruikt: {{states('sensor.carbu_com_<phonenr>_voice_sms')}}%
      ({{state_attr('sensor.carbu_com_<phonenr>_voice_sms','includedvolume_usage')}} van
      {{state_attr('sensor.carbu_com_<phonenr>_voice_sms','total_volume')}})

      ### Totaal data verbruikt: {{states('sensor.carbu_com_<phonenr>_internet')}}%
      ({{state_attr('sensor.carbu_com_<phonenr>_internet','includedvolume_usage')}} van
      {{state_attr('sensor.carbu_com_<phonenr>_internet','total_volume')}})

      #### {{state_attr('sensor.carbu_com_<phonenr>_voice_sms','period_days_left')|int}}
      dagen resterend
      ({{((state_attr('sensor.carbu_com_<phonenr>_voice_sms','total_volume')|replace('
      Min','')) or 0)|int -
      (state_attr('sensor.carbu_com_<phonenr>_voice_sms','includedvolume_usage') or
      0)|int}} Min)
      laatste update: *{{state_attr('sensor.carbu_com_<phonenr>_voice_sms','last update')
      | as_timestamp | timestamp_custom("%d-%m-%Y")}}*
  - type: custom:dual-gauge-card
    title: false
    min: 0
    max: 100
    shadeInner: true
    cardwidth: 350
    outer:
      entity: sensor.carbu_com_<phonenr>_voice_sms
      attribute: used_percentage
      label: used
      min: 0
      max: 100
      unit: '%'
      colors:
        - color: var(--label-badge-green)
          value: 0
        - color: var(--label-badge-yellow)
          value: 60
        - color: var(--label-badge-red)
          value: 80
    inner:
      entity: sensor.carbu_com_<phonenr>_voice_sms
      label: period
      attribute: period_used_percentage
      min: 0
      max: 100
      unit: '%'
  - type: history-graph
    entities:
      - entity: sensor.carbu_com_<phonenr>_voice_sms
    hours_to_show: 500
    refresh_interval: 60
```
</details>
