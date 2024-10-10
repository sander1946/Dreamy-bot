# Dreamy Assistant Bot

## Commands

### Run Management:
Runs are separated per server and there is no maximum amount to runs that can be created in a server, however there can be only one run per person per server

- **/CreateRun `*<guide>` `*<member1>` `<*member2>` `<*member3>` `<*member4>` `<*member5>` `<*member6>` `<*member7>`**
  - This command creates a run with no maximum limit, you can specify the guide of the run, this will default to the one that used the command if not given.
  - The `*guide` must be a @user mention if given. 
  - The vields `*member1` to `*member7` must be a @user mention if provided
  - -# In order to use this command you need to be an Tech Oracle or up, or be one of the following people: @vincediversity, @fanceknight

- **/AddRunners `*<guide>` `*<member1>` `<*member2>` `<*member3>` `<*member4>` `<*member5>` `<*member6>` `<*member7>`**
  - This command updates a run and will resend the run overview, you can specify the guide of the run, this will default to the one that used the command if not given.
  - The `*guide` must be a @user mention if given. 
  - The vields `*member1` to `*member7` must be a @user mention if provided
  - -# In order to use this command you need to be an Tech Oracle or up, or be one of the following people: @vincediversity, @fanceknight

- **/RemoveRunners `*<guide>` `*<member1>` `<*member2>` `<*member3>` `<*member4>` `<*member5>` `<*member6>` `<*member7>`**
  - This command removes members from a certain run based on the guide, you can specify the guide of the run, this will default to the one that used the command if not given.
  - The `*guide` must be a @user mention if given. 
  - The vields `*member1` to `*member7` must be a @user mention if provided
  - -# In order to use this command you need to be an Tech Oracle or up, or be one of the following people: @vincediversity, @fanceknight

- **/SplitRun `<new_guide>` `<*current_guide>` `<*member1>` `<*member2>` `<*member3>` `<*member4>` `<*member5>` `<*member6>` `<*member7>`**
  - This command moves members from 1 run to another run, this can take up to 7 passenger members to move to the new run. This will move the members for the current_guide to the new_guide. the current_guide will default to the one that used the command if not given.
  - The `original_guide` must be a @user mention, and has no default
  - The `new_guide` must be a @user mention, and has no default
  - The vields `*member1` to `*member7` must be a @user mention if provided
  - -# In order to use this command you need to be an Tech Oracle or up, or be one of the following people: @vincediversity, @fanceknight

- **/CloseRun `*<guide>`**
  - This command closes an open run that is currently set. you can set the run leader, this will default to the one that used the command if not given.
  - The `*guide` must be a @user mention if given. 
  - -# In order to use this command you need to be an Tech Oracle or up, or be one of the following people: @vincediversity, @fanceknight