import serial
import RPi.GPIO as GPIO
import time
import math
import os

## Overwrite script
f = open('/var/www/html/script.js','w')
f.write("function initMap() {\n")
f.close()
## Overwrite index.html
g = open('/var/www/html/index2.html','w')
## Headline and link
g.write("<div style=text-align:center><p><span style=font-size:36px;>GPS-info</span><br/>")
g.write("<a href=http://www.copypastemap.com> Go to copypastemap.com</a> or <a href=http://www.hamstermap.com/custommap.html>hamstermap.com</a></p></div>")
g.close()
## Save state
save = 0
## Counter
i = 0
## Naming board pins
LED2 = 32
LED1 = 36
## Save data switch
sw1 = 40
## Shutdown RPI switch
sw2 = 38

GPIO.setwarnings(False)

# Use pin numbers on board
GPIO.setmode(GPIO.BOARD)

GPIO.setup(LED1, GPIO.OUT, initial=0)
GPIO.setup(LED2, GPIO.OUT, initial=0)
GPIO.setup(sw1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(sw2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

## Function sets save mode
def funksjon1(channel):
    global save
    save = 1
    
## Function shutdown    
def funksjon2(channel):
    os.system("sudo shutdown -P now")
 
## Save data
GPIO.add_event_detect(sw1, GPIO.RISING, callback=funksjon1,bouncetime=100)
## Shutdown
GPIO.add_event_detect(sw2, GPIO.FALLING, callback=funksjon2,bouncetime=100)

ser = serial.Serial("/dev/ttyS0")
while(1):
	try:
            d_in=ser.readline()
            ## Split $GPRMC string
            gps_data = d_in.split(',')
            if gps_data[0] == '$GPGGA':
                satellitt = gps_data[7]
            if gps_data[0] == '$GPRMC':
                    if gps_data[2] == 'A':
                            ## Turn on green LED if GPS has fix
                            GPIO.output(LED2, True)
                            ## Calculate latitude
                            ddl = gps_data[3][0:2]
                            ml = gps_data[3][2:4] + gps_data[3][5:8]
                            mml = (int(ml)*100)/60
                            latitude = ddl + "." + str(mml)
                            ## Calculate longitude
                            dda = gps_data[5][0:3]
                            ma = gps_data[5][3:5] + gps_data[5][6:9]
                            mma = (int(ma)*100)/60
                            longitude = dda + "." + str(mma)
                            ## Clock
                            clk_raw = gps_data[1]
                            clk = clk_raw[0] + clk_raw[1] + ":" + clk_raw[2] + clk_raw[3]
                            
                            ## Save GPS data to script file on web server
                            if save == 1:
                                    f = open('/var/www/html/script.js','a')
                                    f.write("var gps"+str(i)+" = {")
                                    f.write("info: '<strong>"+ gps_data[9][0:2] + "." + gps_data[9][2:4] + "."+ gps_data[9][4:6] + "." + "-"+clk+"</strong><br>\',")
                                    f.write("lat: "+latitude+",")
                                    f.write("long: "+longitude+"")
                                    f.write("};\n")					
                                    f.close()
                                    f = open('/var/www/html/script.js','a')
                                    f.write("var gps"+str(i)+" = {")
                                    f.write("info: '<strong>Dato: </strong><i>"+ gps_data[9][0:2] + "." + gps_data[9][2:4] + "."+ gps_data[9][4:6] + "</i>" + "<br/><strong>Klokkeslett: </strong><i>"+clk+"</i><br/><strong>Antall satelitter: </strong><i>"+satellitt+" </i><br>\',")
                                    f.write("lat: "+latitude+",")
                                    f.write("long: "+longitude+"")
                                    f.write("};\n")					
                                    f.close()

                                    ## Color check changes color and form on markers for the map
                                    color_check = i % 2
                                    if color_check == 1:
                                        color = "blue"
                                        form = "circle2"
                                    else:
                                        color = "red"
                                        form = "cross2"
                                    ## Save GPS data to index2 file (text view coordinates) on web server
                                    g = open('/var/www/html/index2.html','a')
                                    g.write("<div style=text-align:center;>" + latitude + "\t" + longitude + "\t" + form + "\t" + color + "\t" + str(i) + "\t" + gps_data[9][0:2] + "." + gps_data[9][2:4] + "." + gps_data[9][4:6] + "." + "-" + clk + "</div>")
                                    g.close()					
                                    save = 0
                                    i = i + 1
                                    ## Print to screen when data is saved
                                    print "Data saved"
                                    ## Blink red LED when data is saved
                                    GPIO.output(LED1, True)
                                    time.sleep(0.2)
                                    GPIO.output(LED1, False)
	except KeyboardInterrupt:		
            ## On CTRL+C followed by CTRL+Z: write rest of javascript to file
            f = open('/var/www/html/script.js','a')
            f.write("var locations = [")
            for a in range(i):
                f.write("[gps"+str(a)+".info, gps"+str(a)+".lat, gps"+str(a)+".long, "+str(a)+"],\n")

            f.write("];\n")
            f.write("var map = new google.maps.Map(document.getElementById('map'), {\n")
            f.write("zoom: 13,\n")
            f.write("center: new google.maps.LatLng("+latitude+", "+longitude+"),\n")
            f.write("mapTypeId: google.maps.MapTypeId.HYBRID\n")
            f.write("});\n")
            f.write("var infowindow = new google.maps.InfoWindow({});\n")
            f.write("var marker, i;\n")
            f.write("for (i = 0; i < locations.length; i++) {\n")
            f.write("marker = new google.maps.Marker({\n")
            f.write("position: new google.maps.LatLng(locations[i][1], locations[i][2]),\n")
            f.write("map: map\n")
            f.write("});\n")
            f.write("google.maps.event.addListener(marker, 'click', (function (marker, i) {\n")
            f.write("return function () {\n")
            f.write("infowindow.setContent(locations[i][0]);\n")
            f.write("infowindow.open(map, marker);\n")
            f.write("}\n")
            f.write("})(marker, i));\n")
            f.write("}\n")
            f.write("}\n")
            f.close()
ser.close()
