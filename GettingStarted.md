Getting Started with Philips Hue DSLink
Guide written by Robin Prussin(Robin.Prussin@stuartolson.com)

This getting started guide is designed to guide a new user through the setup process of dslink-python-hue written by Logan Gorence https://github.com/logangorence

1. Download ZIP of dslink-python-hue  (https://github.com/IOT-DSA/dslink-python-hue)
2. Login to your DGLux Server as Super User (dgSuper)
3. Under Data->sys->links   Right Click and select Install Link->from ZIP
4. Select the ZIP of dslink-python-hue from your download folder and click invoke. You should receive a success indication.
5. Your new link will appear under Data->sys->links. Make sure your link is started. Setup of the link requires write permissions and a python package "setuptools". Any errors will appear in the log.
6. Once your link is started it will appear under Data->downstream->PhillipsHue
7. Right click the link and select Add Bridge.
8. Name your bridge and input the host address. Ex 10.0.0.25     Note: You do not have to enter any other switches or paths. Click invoke.
9. You should now have your brdige under Data->downstream->PhillipsHue->MyBridgeName
10. The hue bridge status should report "Not Registered". This is because the connection must be authenticated by the bridge. To do this, press the pairing button on your Hue bridge, then quickly right click on your bridge link in DGLux and select reconnect.
11. Your status should change to "Connected". The link will then discover any lights connected to your bridge and present their controls under the metrics window.
12. Build your application controls to control the lights.

