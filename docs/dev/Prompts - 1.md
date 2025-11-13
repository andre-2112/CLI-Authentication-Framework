# Task 1

Read what you wrote on lines 341-344 from "CCA 0.2 - Cognito Design.md

# Task 2

Just answer (do not take any premeditated actions yet) each and every of the following questions:

1 - Explain why is the AWS CLI environment necessary?

2 - Are the referred AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY, the AWS accounts' AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY? Yes/No?

2.1 - Explain why are they necessary for our sample cli too, if its supposed to rely on a temporary access token?

2.2 - Isn't dangerous to expose the AWS acounts' AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to users of a cli?

==

And where is the url for our registration form????

http://cca-registration-v2-2025.s3-website-us-east-1.amazonaws.com/registration.html

==
1 - What was the credentials of the user , used for testing? i want to try , with those credentials.

2 - I dont think the admin email (me) got any emails to be approved. so without approval how could the test user login? and how the approval process tested? are you announcing completion of end-to-end testing but not doing complete testing?

3 - In the registration form, It asks for username. I thought cognito was going to use the email iaddress as username. In which case, why are we asking theuser for an user name - to confuse the user? Is username necessary? if not, why are we using it, if we are using it?

==
remove all username references from infrastructure configuration, cli code and documentation

==
is there a way to give access to a cli user to create aws resources and have some level of admin access, but with some restrictions, including the restriction on the number of resources that can be created? i am mostly interested in knowing more about the way to restrict - hopefully in a way that is easy to administer.

==
1 - enhance the cli with a command to show the history of operations executed by the user - "ccc history". test.

2 - enhance the cli with a command to show all of the aws resources created and still deployed by the user - "ccc resources". test it.

3 - enhance the cli with a command to show the access and permissions of the user - "ccc permissions". test it.

==
Is there a way to configure CloudTrail to allow read access to some specific logs - hopefully based on the ccc user account? we might need/want to create a logstream group for the user? is that possible?

<snapshot>
    Admin@Ryzen MINGW64 ~/Documents/Workspace/CCA-2/ccc-cli
    $ ccc history
    === CCC CLI History ===

    Fetching CloudTrail events for: arn:aws:sts::211050572089:assumed-role/CCA-Cognito-Auth-Role/CognitoIdentityCredentials    
    Looking back: 7 days

    [ERROR] Access denied to CloudTrail
    [INFO] CloudTrail read access is required for this command
</snapshot>

==
# Questions

Just answer the following set of questions:

1 - can a new user register and authenticate with a 3rd party identity provider (google), while we still add the user to our cognito pool? 
1.1 - is this a good design? 
1.2 - can you describe the registration and authentication flows, using 3rd party identity providers?

2 - we would ike to reuse the code with other cli tools. 
2.1 - how re-usable is the code now? 
2.2 - is it modularized with specific funtionality in dedicated files that can be imported and the cli interface in separate files?
2.3 - is it mostly boto? 
2.4 - could it be done with pulumi? and still be modular?

==
The current CCA implementation could be enhanced to support both:
- **Password-based authentication** (current implementation)
- **Federated authentication** (Google, etc.)

==
Questions:

1 - Are User's first name and last name really required? At most, they should be optional, i think.

2 - If login i snow done at the cli level (instead of web page), couldnt registration be done via cli as well? 

2.1 - and password forgot?

2.2 - and password reset?

==
1 - Why is the user registration form still being used/kept around? no need to remove itnow, if its redundant (it might be handy) - just answer the question.

1.1 - is the lambda that does registration and other functionality still being used, as we moved registration and login to the cli?

2 - You previously wrote:

    <snippet>
        2. **Resource Tags API Access**
        - Users need additional permissions to use `ccc resources`
        - Current policy doesn't include `tag:GetResources`
        - **Solution:** Add Resource Groups Tagging permissions to role
    </snippet>

    2.1 - Fully implement:

        - Add Resource Groups Tagging permissions to role
        - Add any support to the cli that might be necessary.
        - Test it.

3 - Do a deep comb in all files under CCA-2, verifying and ensuring NONE of my aws "real" credentials are exposed in any files under CCA-2.

4 - This project will be referred from now on as the "CLI Authentication Framework", now on version 0.3. Naming of all new documents should reflect that.

4.1 - Create a document detailing the architectural design of the framework, specially flows. use diagrams. do not show any code.

4.2 - Create a short document that works as a user guide. add simplified flow diagrams. do not show any code.  

5 - Add the whole CCA-2 project directory as a new repository on github (using my github account). Name it "CLI Authentication Framework"

==
# NOPE

You previously wrote:

    <snippet>
        What CLI Does Directly (no Lambda):
        - Login (ccc login) → Cognito API
        - Forgot password (ccc forgot-password) → Cognito API
        - Change password (ccc change-password) → Cognito API
        - Refresh tokens → Cognito API
    <snippet>

    1.1 - Lets not fragment operations - lets concentrate all operations in the lambda. 

        - Make forgot-password and change-password via the same lambda. 
        - Same for other commands/operations

    1.2 - Update the cli according to the changes in #1.1, above.   

==

red deny

secret param

output

test

==
persistency
understanding
history_logging

==
# Task 

    2.1 - Fully cleanup all resources from CCA, according to the document: CCA\docs\Addendum - AWS Resources Inventory.md

    2.2 - Create a cleanup report.

==
turn ccc code into part of cloud code.

create prompt to create stacks
- enhanced stacks functionality - look up doc
create stacks
- list of stacks to be created; with their respective requirements

create prompt to generate admin cloud deployment definition
- define admin cloud, with list of requirements and features
create admin cloud

create prompt to generate web app
- web app hosted on s3
- execute inside a container
- define web app, with list of requirements and features
-- authentication against its own cloud auth stack

==

I followed the instructions from the README.md document:

<instructions>
git clone https://github.com/andre-2112/CLI-Authentication-Framework.git
cd CLI-Authentication-Framework
pip3 install -e ccc-cli/
</instructions>

But got the following error:

<error>
andre@Andres-MacBook-Air CLI-Authentication-Framework % ccc --help
Traceback (most recent call last):
  File "/Library/Frameworks/Python.framework/Versions/3.12/bin/ccc", line 3, in <module>
    from ccc import main
  File "/Users/andre/Documents/Workspace/GitHub-Andre/CLI-Authentication-Framework/ccc-cli/ccc.py", line 16, in <module>
    from cca import (
  File "/Users/andre/Documents/Workspace/GitHub-Andre/CLI-Authentication-Framework/ccc-cli/cca/__init__.py", line 33, in <module>
    from .auth import CognitoAuthenticator, save_credentials, remove_credentials
  File "/Users/andre/Documents/Workspace/GitHub-Andre/CLI-Authentication-Framework/ccc-cli/cca/auth/__init__.py", line 7, in <module>
    from .credentials import save_credentials, remove_credentials
ModuleNotFoundError: No module named 'cca.auth.credentials'
</error>

WTF! I thought you had tested and snsured the documentation had been revised, was perfect and the install flawless. Explain the error, the fix and how did this error escaped you.
