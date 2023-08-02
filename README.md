# ISSEM_Lab4

Vulnerabilities List:


| Vulnerability  | Point Person  |  Status       | Note       | 
| -------------  | ------------- | ------------- | ------------- |
| SampleNetworkClient.py  
| -------------  | ------------- | ------------- | ------------- |
| DDoS Counter/rate limiter (SampleNetworkClient.py)   | Content Cell  | Open  | ------------- |
| No Protection from System Clock Manipulation   | Content Cell  | Open  | ------------- |
| TLS to secure NW communication   | Content Cell  | Open  | ------------- |
| Vulnerability in the OS library   | Content Cell  | Open  |  1 |
| Init Declarations and Initializations   | Content Cell  | Open  |  3 |
| -------------  | ------------- | ------------- | ------------- | 
| SampleNetworkServer.py 
| -------------  | ------------- | ------------- | ------------- | 
| socket.recfrom blocks until data is received  | Content Cell  | Open  | 2 |
| TLS to secure NW communication   | Content Cell  | Open  | ------------- |
| TLS to secure NW communication   | Content Cell  | Open  | ------------- |
| Vulnerability in the OS library   | Content Cell  | Open  |  1 |
| DDoS counter/rate limiter (SampleNetworkServer.py)  | Content Cell  | Open  | ------------- |
| Content Cell   | Content Cell  | Open  |  ------------- |
| Content Cell   | Content Cell  | Open  | ------------- |
| Content Cell   | Content Cell  | Open  |  ------------- |


Notes:
1. Directory traversal that could allow attackers to potentially gain system access. https://www.bleepingcomputer.com/news/security/unpatched-15-year-old-python-bug-allows-code-execution-in-350k-projects/
2. Can cause a program hang. We should be using a timeout
3. self.infTemps and self.incTemps are not initialized in the init
