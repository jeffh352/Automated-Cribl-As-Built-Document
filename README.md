Hello! Here is a basic rundown of what you need and how to use this script!

Prerequisites:
    Python version 3.x
    Python Libraries:
        docx
        datetime
        math
        csv
        json
        requests

# How to Use
Cribl Version: 4.4.3

Run the Word_docx_creation.py script and it will prompt you to enter a number that will either be:
1) For As Built Document
2) For Stream Health Document
Then you type in your Client's Name along with the name of the Consultant.

It will ask for a Client Name and a Consultant Name, enter accordingly.

After this you will have to enter a URL which should look like "https://main-optimistic-khayyam-hejde16.cribl.cloud", make sure there are no / at the end of the link as this will cause an error in the code
If you are using a docker instance then your URL will most likely look like "http://localhost:9000"

Once these values have been passed it will ask you three(3) type of ways to authenticate your login, these are
1) Username and Password        -   To login using username and password, this is usually used for Docker environments and does not usually work in Cloud environments
2) Bearer Token                 -   To use the bearer token found on your environments API Call tab, go to your Cribl home page then go to Settings->Global Settings->API Reference and it  should be found in an API call you make under the curl command after Authorization: Bearer and should look like this:"eyJhbGciOiJSU..."
3) Client ID and Client Secret  -   To use the clients API credentials by going to Cribl clouds home page then on the to left go to Account->Organization->API Management then your credentials should be there or if not then you'd have to create one

Any bugs or issues found, please report!
