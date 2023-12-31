# Group 15 - ISSEM

Note: These are NEW vulnerabilities building on top of the patches already performed in previous labs

### Vulnerabilities List


| **Vulnerability**  | **Point Person**  |  **Status**       | **Note (details)**       | 
| -------------  | ------------- | ------------- | ------------- |
| <ins>**SampleNetworkClient.py**</ins> 
| -------------  | ------------- | ------------- | ------------- |
| DoS Counter/rate limiter (SampleNetworkClient.py)   |  Alon Hillel-Tuch   | patched  | ------------- |
| No Protection from System Clock Manipulation   | Content Cell  | Open  | 12 |
| TLS to secure NW communication   | Alon Hillel-Tuch  | Patched  | ------------- |
| Vulnerability in the OS library   | Content Cell  | Open  |  1 |
| socket.recfrom blocks until data is received  | Content Cell  | Open  | 2 |
| Init Declarations and Initializations   | Content Cell  | Open  |  3 |
| Error Handling   | Alon Hillel-Tuch  | Patched  |  6 |
| Temperature Management   | Copeland Myrie |  Open |  11 |
| -------------  | ------------- | ------------- | ------------- | 
| <ins>**SampleNetworkServer.py**</ins> 
| -------------  | ------------- | ------------- | ------------- | 
| socket.recfrom blocks until data is received  | Content Cell  | Open  | 2 |
| TLS to secure NW communication   | Alon Hillel-Tuch  | Patched  | ------------- |
| Vulnerability in the OS library   | Content Cell  | Open  |  1 |
| DDoS/Dos counter/rate limiter (SampleNetworkServer.py)  |  Alon Hillel-Tuch   | Patched  | ------------- |
| Input Validation  | Copeland Myrie  | Open  |  4 |
| Access Controls  | Copeland Myrie | Open  | 5 |
| Error Handling   | Alon Hillel-Tuch | Patched  |  6 |
| Token Storage  | Content Cell  | Open  |  7 |
| Token Usage  | Content Cell  | Open  |  8 |
| Timing Attack  | Content Cell  | Open  |  9 |
| Poor Randomness  | Alon Hillel-Tuch  | Patched  |  10 |
| Temperature Management   | Copeland Myrie |  Open  |  11 |
| -------------  | ------------- | ------------- | ------------- |

LACK OF ERROR LOGGING!

Status types:
[Open, Patched, Closed]
Closed implies the patch has been tested. 

Notes:
1. Directory traversal that could allow attackers to potentially gain system access. https://www.bleepingcomputer.com/news/security/unpatched-15-year-old-python-bug-allows-code-execution-in-350k-projects/
2. Can cause a program hang. We should be using a timeout
3. self.infTemps and self.incTemps are not initialized in the init
4. There is no input validation performed on the values passed to the smartnetworkthermometer class. Same issue with processCommands(), For each command, the method checks if it is one of several predefined commands, such as "AUTH", "LOGOUT", "SET_DEGF", "SET_DEGC", "SET_DEGK", "GET_TEMP", or "UPDATE_TEMP". If the command is recognized, the method performs the appropriate action, such as authenticating the client, logging out the client, setting the temperature unit, or updating the current temperature. Malformed or unexpected commands sent to the server, could cause unexpected behavior or errors.
5. The processCommands() method does not appear to implement any access controls to prevent unauthorized clients from executing certain commands. Any client can send a "SET_DEGF", "SET_DEGC", or "SET_DEGK" command to change the temperature unit used by the server, even if they are not authenticated.
6. Lack of error handling. The code does not include any error handling for situations where an exception might be raised, such as when attempting to bind the socket to an already-used port or when attempting to read from an environment variable that does not exist. This could cause the script to crash or behave unexpectedly if an error occurs.
7. The processCommands() method stores authentication tokens in a dictionary as an instance variable of the SmartNetworkThermometer class. The dictionary is not protected. An attacker with access to the server’s memory to read the authentication tokens and use them to impersonate legitimate clients.
8. The method uses a simple token-based authentication system to authenticate clients. While this can provide some level of security, it may not be sufficient for sensitive applications.
9. The processCommands() method includes an "AUTH" command that allows clients to authenticate by sending a password. However, the password is compared to the value returned by the authenticate() method using the == operator, which can be vulnerable to timing attacks. A more secure approach would be to use a constant-time comparison function, such as hmac.compare_digest(), to compare the password values.
10. The random.choice() module is not suitable for generating secure random values, as it uses a deterministic algorithm that can be predicted by an attacker. A more secure approach would be to use the secrets module, which provides functions for generating cryptographically secure random values.
11. There is no validation that the set temperature commands are with acceptable parameters, we can deliberately freeze or overheat the infant. 
12. Potential solutions include to prevent system clock/time tampering include: (a) Using a Secure Time Source: To mitigate clock manipulation, consider using a reliable and secure time source, such as an NTP (Network Time Protocol) server. NTP can help ensure that your system's clock remains accurate and is less susceptible to manipulation. (b) Alongside the token-based system, we can also include a timestamp in each request. The server can validate that the timestamp is recent and within an acceptable range from the server's perspective. If the timestamp is too far in the past or the future, the request can be rejected. (c) Implement server-side validation of the received timestamp and token. This involves verifying that the timestamp is recent and valid and that the token is associated with the correct timestamp. If either check fails, the server should reject the request. (c) is similar to solution (b), but server side.
13. 
Stylistic Concerns:
The code uses a lot of 'magic numbers' that is, non-descript constants within the code such as 30,500, etc. They should be named constants instead and define the constants clearly up top.


Environment Concerns:

1. We do not know what version of libraries are being used.
2. We know that the code runs on the Linux operating system but we do not know what version of Linux and what dependencies have been installed. 
3. We do not know what the network layout is. [we're just manufacturing the device, so we do not know what type of network it will be put in, so expect the worst]
4. We do not know what the greater authentication system is




Patch Notes:

- Random.choice(): this function has been removed. Instead, the code uses the secrets.choice() method to generate a random token, secrets.choice() generates cryptographically secure random values, which is more secure than the deterministic algorithm used by random.choice(). 
