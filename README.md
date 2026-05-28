# Open SmartCity Home HACS Integration

<div style="display:flex;gap:1%;margin-bottom:20px">
  <img height="100px" alt="logo" src="logo.svg">
</div>

⚠️ **Beta Software**
This integration is currently in **beta**. Functionality, configuration flow, and entity structure may change. Use at your own risk.

## Overview

The **Open SmartCity Home Home Assistant Integration** connects Open SmartCity Home sensor stations to Home Assistant.
Each selected station is represented as a **device**, with its sensors exposed as **entities**.

---

## Prerequisites

* Home Assistant
* **HACS (Home Assistant Community Store)** installed

Install HACS by following the official instructions:
👉 [https://hacs.xyz](https://hacs.xyz)

---

## Installation

### Manual Installation (via Custom Component)

1. Clone this repository into your Home Assistant configuration directory:

   ```
   config/custom_components/open_smartcity_home
   ```

   The final structure should look like:

   ```
   config/
     custom_components/
       open_smartcity_home/
         __init__.py
         manifest.json
         ...
   ```

2. Restart Home Assistant.

---

## Configuration

1. Open the Home Assistant UI.
2. Go to **HACS**.
3. Click on the 3 dots in the top right corner.
4. Select **Custom repositories**.
5. Add the URL **https://github.com/Klingenstadt-Solingen/Open-SmartCity-Home-HACS-Integration** to the repository and select Type **Integration**.
6. Click the **ADD** button.
7. Go to **Settings → Devices & Services → Integrations**.
8. Click **Add Integration**.
9. Search for **Open SmartCity Home**.
10. Select the integration.

You will be prompted to **select the sensor stations** you want to add.

---

## Devices & Entities

After confirming the configuration:

* A **device** will be created for **each selected sensor station**
* An **entity** will be created for **each sensor** belonging to that station

You can now use the entities in dashboards, automations, and scripts.

---

## Notes

* This integration is in **beta**
* Entity IDs and naming may change
* Error handling is still limited
* Feedback and bug reports are welcome

---

## License

This project is licensed under the [Open Smart City License](LICENSE.md).

## Legal notices and data reliability

Before using the data, please note the legal information [here](Legal-Notices-and-Data-Reliability.md).
