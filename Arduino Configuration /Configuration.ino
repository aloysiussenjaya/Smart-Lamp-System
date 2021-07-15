#include <ESP8266WiFi.h>

// NOTE: In this configuration HIGH means Off and LOW means On 

// Initialize Port Number
int port = 8888;

// Define WiFi Network
const char *ssid = "MI 8";  //WiFi SSID
const char *password = "qwerty123";  //WiFi Password

// Create WiFi Server listening on the given port 
WiFiServer server(port);

// Setup and Loop Function are mandatory in Arduino Code

// Function that run once 
void setup() {
  // Start serial communication with the given baud rate. 

  Serial.begin(115200);

  // Set WiFi to Station Mode
  WiFi.mode(WIFI_STA);
    
  // Connect to WPA/WPA2 network. 
  WiFi.begin(ssid, password);

  // Set lamp off
  pinMode(D1, OUTPUT); // Set D1 Pin as Output
  digitalWrite(D1, HIGH); // Set D1 Pin Off


  // Connect to WiFi Network.
  while(WiFi.status() != WL_CONNECTED){
    Serial.println("Connecting to Network named: ");
    Serial.println(ssid);

    // amount of time to wait for connection in ms. 
    delay(1000);
    
  }

  // Start the server. 
  server.begin();

  // Print WiFi status.
  printWifiStatus();
  
}

// Function that would run repeatedly after setup function done 
void loop() {
  // Check that we are connected.
  if(WiFi.status() != WL_CONNECTED){
    return;
  }

  // Listen for incoming client requests.
  WiFiClient client = server.available();
  if(client){
    if(client.connected()){
      Serial.println("Client connected");
    }

    while(client.connected()){
      while(client.available()>0){
        String request = readRequest(&client);
        Serial.println("");
        Serial.println(request);
        executeRequest(&client, &request);
        String response = "It's working fine";
        sendResponse(&client, response);
      }
    }
    
    // Close the connection.
    client.stop();

    Serial.println("Client disconnected");
    Serial.println("");
    Serial.println("");
  }
}

// Receive message from the client 
String readRequest(WiFiClient* client){
  String request = "";

  // Loop while the client is connected.
  while(client->connected()){
    // Read available bytes. 
    while(client ->available()){
      // Read a byte.
      char c = client->read();

      // Print the value (for debugging).
      Serial.write(c);

      // Exit loop if end of line. 
      if('\n' == c){
        return request;
      }

      // Add byte to request line.
      request += c;
    }
  }
  return request;
}

// Execute message from client to decide state of the lamp (ON or OFF)
void executeRequest(WiFiClient* client, String* request)
{
  char command = readCommand(request);
  int n = readParam(request);
  Serial.println("");
  Serial.print("Request from Client Socket");
  Serial.println(command);
  if ('1' == command)
  {
    // Set lamp off
    Serial.println("Execute Lamp Off");
    digitalWrite(D1,HIGH);  // Set D1 Pin Off
    Serial.println(digitalRead(D1)); 
  }
  else if ('0' == command)
  {
     // Set lamp On
     Serial.println("Execute Lamp On");
     digitalWrite(D1,LOW);  // Set D1 Pin On
     Serial.println(digitalRead(D1));
  }
}

// Function to read the command from the request string.
char readCommand(String* request)
{
  String commandString = request->substring(0, 1);
  return commandString.charAt(0);
}

// Function to read the parameter from the request string.
int readParam(String* request)
{
  // This handles a hex digit 0 to F (0 to 15).
  char buffer[2];
  buffer[0] = request->charAt(1);
  buffer[1] = 0;
  return (int) strtol(buffer, NULL, 16); // Convert to long integer
}

// Function to send the response message
void sendResponse(WiFiClient* client, String response)
{
  // Send response to client.
  client -> println(response);

  // Print the response (for debugging)
  Serial.println("sendResponse:");
  Serial.println(response);
}

// Function to show WiFi Status 
void printWifiStatus(){
  Serial.println("WiFi status"); 

  // Print network name.
  Serial.print(" SSID: ");
  Serial.println(WiFi.SSID());

  // Print WiFi shield IP Address.
  Serial.print("IP Address : ");
  Serial.println(WiFi.localIP());

  // Print WiFi Port 
  Serial.print("Port : ");
  Serial.println(port);

  // Print the signal strength.
  long rssi = WiFi.RSSI();
  Serial.print(" Signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
}