# Sycamore
Python scripts to extract entire student body data from Sycamore.

## Prerequisites

Install prerequisites through pip:
```
pip install pandas
pip install phonenumbers
pip install urllib3
pip install certifi
```

If using a Python environment that is externally managed (e.g. on Debian),
install with the system's package manager:
```
sudo apt install python3-pandas python3-phonenumbers
```


## Access Token

Reading data from the Sycamore API requires an access token. This can be
created in the Sycamore UI at My Organizer -> Utilities -> Applications -> Access Tokens


## Operation

This example shows how to generate SDS 2.1 import data from Sycamore:

```
cd src/sds
python3 ExtractFromSycamoreToSDS21.py --school 2132 --cache cache --out outv21 --token [sycamore token]
```

This command uses an existing Sycamore cache in the `cache` directory. If that
does not exist or is incomplete, the directory is created and data from Sycamore
is downloaded. It write output data to the `outv21` directory. The folder is
created if it does not exist.

# PowerShell
See [src/powershell/README.md](src/powershell/README.md).
