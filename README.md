# ride-proxy-server

To run the server on your local, you need to generate a self-signed certificate using openssl with a config file `san.cnf`. Modify the `stateOrProvinceName` and `localityName` in the example file below: 

```
[req]
default_bits  = 2048
distinguished_name = req_distinguished_name
req_extensions = req_ext
x509_extensions = v3_req
prompt = no
[req_distinguished_name]
countryName = US
stateOrProvinceName = <CA>
localityName = <San Francisco>
organizationName = Lyft
commonName = 120.0.0.1: Self-signed certificate
[req_ext]
subjectAltName = @alt_names
[v3_req]
subjectAltName = @alt_names
[alt_names]
IP.1 = 10.0.2.2
```

Run this command to generate the certificate:

```
openssl req -x509 -nodes -days 730 -newkey rsa:2048 -keyout key.pem -out cert.pem -config san.cnf
```

It will generate 2 files: `cert.pem` and `key.pem`. Set the value of `CERT_FILE` and `KEY_FILE` to be the paths of `cert.pem` and `key.pem` in `app/httpserver.py`


Copy the content of `cert.pem` and replace [this file](https://github.com/lyft/instant-android/blob/poc_in_ride_testing/apps/driver/src/debug/res/raw/my_ca) in android repo to make https request from client to this server work. 