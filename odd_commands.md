# Dreamy Assistant Bot

## Commands

### Run Management:

- **/CreateRun `*<guide>` `*<member1>` `<*member2>` `<*member3>` `<*member4>` `<*member5>` `<*member6>` `<*member7>`**
  - This command creates a run with no maximum limit, you can specify the guide of the run, this will default to the one that used the command if not given
  - The `*guide` must be a @user mention if given. 
  - The vields `*member1` to `*member7` must be a @user mention if provided
  - -# In order to use this command you need to be an Tech Oracle or up, or be one of the following people: <@152948524458180609>, <@496387339388452864>

- **/AddRunners `*<guide>` `*<member1>` `<*member2>` `<*member3>` `<*member4>` `<*member5>` `<*member6>` `<*member7>`**
  - This command updates a run and resends the run overview, you can specify the guide of the run, this will default to the one that used the command if not given
  - The `*guide` must be a @user mention if given. 
  - The vields `*member1` to `*member7` must be a @user mention if provided
  - -# In order to use this command you need to be an Tech Oracle or up, or be one of the following people: <@152948524458180609>, <@496387339388452864>

- **/CloseRun `*<guide>`**
  - This command closes an open run that is currently set. you can set the run leader, this will default to the one that used the command if not given
  - The `*guide` must be a @user mention if given. 
  - -# In order to use this command you need to be an Tech Oracle or up, or be one of the following people: <@152948524458180609>, <@496387339388452864>

## NOT IMPLEMENTED
- **/RemoveRunner `<member>` `*<guide>`**
  - This command removes members from a certain run based on the guide, if not set it will default to <@152948524458180609> seen that he is the main runner.
  - The `member` must be a @user mention
  - The `*guide` must be a @user mention if given. 
  - -# In order to use this command you need to be an Tech Oracle or up, or be one of the following people: <@152948524458180609>, <@496387339388452864>

- **/SplitRun `<original_guide>` `<new_guide>` `<member1>` `<*member2>` `<*member3>` `<*member4>` `<*member5>` `<*member6>` `<*member7>`**
  - This command moves members from 1 run to another run, this can take up to 7 passenger members to move to the new run. This will move the members for the original_guide to the new_guide.
  - The `original_guide` must be a @user mention, and has no default
  - The `new_guide` must be a @user mention, and has no default
  - `member1` must be a @user mention, and has no default
  - The vields `*member2` to `*member7` must be a @user mention if provided
  - -# In order to use this command you need to be an Tech Oracle or up, or be one of the following people: <@152948524458180609>, <@496387339388452864>