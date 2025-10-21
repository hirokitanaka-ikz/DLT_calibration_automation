# DLT calibration automation
Automated calibration measurment of differential luminescence thermometry using a closed-cycle helium cryostat controlled with LakerShore Model335.

## Instrument
This program requires the following two instruments:
- Ocean Optics spectrometer
- Lake Shore Model 335 Cryostat Temperature Controller

### Instrument drivers
- Ocean Optics spectrometer:
Download OmniDriver 2.75 from [Ocean Optics webpage](https://www.oceanoptics.com/software/resources/discontinued-software/) before connecting the spectrometer to the PC. If the spectrometer was connected before the installation of the driver, please uninstall the driver in the device manager.
- Lake Shore temperature controller (USB driver):Go to [Lake Shore webpage](https://www.lakeshore.com/resources/software/drivers?srsltid=AfmBOoqHU2RPusnioFgulbqcSZtUtCAOASqKtducyvpFelJi5qa4p3H3) and download and install the USB driver.


## Running program
### Python environment
- This program uses [uv](https://docs.astral.sh/uv/getting-started/) as a Python package manager. 
- Install uv on your PC following the [instruction](https://docs.astral.sh/uv/getting-started/installation/).

### Quick start guide
execute following command in a shell
```
uv run python main.py
```


