# Contributing
This document was established to have a universal way to publish modifications to the source code so that everyone would understand. \
This also works as a guide for new beginners to understand how the code organization works

Index
 - [Project Explanation](#project-explanation)
 - [Collaborating to the project](#collaborating-to-the-project)
 - [Milestones](#milestones)
 - [Good commit structure](#commit-structure)
 - [Refactoring rules](#code-refactoring)

## Project Explanation
Let's start by saying that if you're on this repository you should also have access to the [repository's project](https://github.com/users/zDany01/projects/10), if not please contact the repository administrators. \
Every type of change to the code is treated as an issue, this includes
 - bug fixes
 - feature requests
 - dependency updates
 - enhancements to existing code

This helps us add more information and manage these changes using GitHub and Git comments ([more on this later](#commit-structure))

### Project Board
The project board has 5 different views
#### Backlog - Table view
This is a table view of the current open issues/drafts that are (or will be) integrated into the project. \
This view contains 5 columns each of which has a different meaning
1. Backlog represents all the drafts that will be opened in the future or active issues that for some reason can't be worked on at that moment
2. Ready contains all the issues that are ready to be taken and resolved, this is the column that most of you will often use
3. In progress is a column where we move the issues when we actively work on them
4. In review is the column where all the completed issues will be put for reviewing before merging, in a nutshell when you create a pull request you should put your issue here
5. Done represent all the currently integrated modifications, normally when an issue is marked as done it should never leave again that column

#### Team Items - List view
This is a view that can be used to view all the issues in a list to better visualize which ones are assigned to whom, it contains all the details of the previous one but in a schematic way

#### Roadmap - Milestone view
This view puts all the open/closed issues in a timeline to view how much time was needed to close an issue and when they were closed, this is often used when milestones are present to have an idea of how much time remains and have a general view of the project in time.

#### In review
This is a simple list of all the items that are currently under review, added for quick access

#### My Items
A shortcut list to see which issues are currently assigned to yourself

### Issues
Every issue on the board has different attributes that help us get more information and distinguish them.
These are:
 1. Assignees - the people that work on that specific issue
 2. Labels - that describe the type of issue that is worked on like
    - addition -> indicate a new feature
    - bug -> something that is not working and needs to be fixed
    - documentation -> this issue requires an update to the documentation
    - duplicate -> this issue is a duplicate of another
    - enhancement -> a feature that improves existing ones
    - good first issue -> an encouragement for new people to help ;)
    - help wanted -> used when you need assistance to manage that issue
    - invalid -> something is wrong and requires more details or understanding
    - question -> further information is required to find a solution or determine the problem
    - wontfix -> this issue will not be worked on for this project
 3. Priority - that indicates how much importance should be given to that issue
    - Null/not declared -> implies that the issue should be treated like others
    - P2 -> It would be good if this issue is resolved first because it would allow faster development of the project or this issue represents a non-interruptive bug that damages the user experience
EX:  string not displayed properly that could annoy the user (but still not incapacitate it to read the information)
    - P1 -> there is an issue that does not allow the program the work properly and limits user interaction but still allows the bot as a whole to work with its essential function
    - P0 -> This is **URGENT**, there is a **MAJOR** outage of functionalities, *the bot **CANNOT** or **SHOULD NOT** be started*. \
    This also includes potential bugs that could HARM in any way the hosting computer. \
    P0 should be treated as a *nuclear issue*, every developer should stop their work and focus on this issue before everything else so we hope to never see an issue with this priority.
 4. Size - this refers to how much time is needed to apply the changes that the issue requires
    - XS -> this is a very small change that only requires adding a single function or adapting existing code
    - S -> this is not a very large change but probably requires a bit of testing or modifying the user interface
    - M -> used when modifying a big part of the code or adding a major feature that requires a lot of testing, this tag is often used for refactoring commit
    - L -> this requires a large recode of existing code, changing or replacing major functions and restructuring the entire logic of some classes or algorithms, in normal circumstances an added feature should never have this impact on the code
    - XL -> this requires an (almost) complete rewrite of the code, used when changing the basic structure of the program, like changing the underlying telegram bot API
 5. Start date - the date where this issue was first worked on, this should be updated the first time an issue is moved from Ready to In Progress
 6. End date - the date when the issue was closed, this should only be updated when the issue status is Done
 7. [Milestone](#milestones) - the milestone which includes this issue (optional)
 8. Development - the current branch used to develop the issue, you should update this when creating a pull request (recommended)
 

## Collaborating to the project
To collaborate on this project you can create an issue or work on an existing one
The project workflow should be the following
1. Choosing an issue from the Ready Tab
2. Moving the issue from Ready to In progress
3. Assigning the issue to yourself
4. Setting the start date of the issue
5. Create a branch locally where applying and testing code changes (See [commit structure](#commit-structure))
6. Upload your branch to GitHub
7. Set the Development attribute to the uploaded branch and open a Pull Request
8. Move your issue to the Review Tab \
From here the issue can be \
8a. Moved back to In progress to modify something in the code 🔄\
8b. Approved and merged into the main branch
9. Unassign yourself from the issue and set an end date

## Milestones
Milestones are simply goals to reach in a defined amount of time, they often coincide with a software release but are not required to.
You should work only on issues that are present in the next milestone to be completed, if present

## Commit structure
It is better to have a unified commit structure so that everyone knows how to read a commit and shouldn't have any problem creating a commit message.
A generally good rule of thumb is that commits shouldn't be too small or too large, for example, you should not create a commit for each update you do to a file or create one that combines 2 new functions.
For this reason, a good structure to follow is the following
```
Descriptive Title

Added

Improved

Changed

Fixed

Removed

Refactored


(Eventual closing reference or co-authoring)
```
To see real examples of this commit structure you can read this commit messages ([1](https://github.com/zDany01/Bassolino-INC/commit/3a2241646eaa6f5c3a7eb888951eb344fcc8ea96), [2](https://github.com/zDany01/Bassolino-INC/commit/d664900647193fa04b143e1b873f066fb0efba71), [3](https://github.com/zDany01/Bassolino-INC/commit/5f122d460859c1b722f592dd370a7101acc62155)) or simply browse the history of the project. \
You can also close an issue by appending Closes #<IssueNumber> at the end of your last commit message. See [GitHub docs](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue#linking-a-pull-request-to-an-issue-using-a-keyword) for more info

## Code Refactoring

Code Refactoring is a term used to describe changes to the code that have minimal impact on its functionality but make it more readable or simple to modify later, it also refers to fixes applied to the code that do not change its logic sense (ex fixing a typo in a string). It should be organized in this way by dividing it into two groups

### Aesthetic only
These are changes that do NOT modify the logic of the code but just the aspect \
Ex:
 - Replacing a variable name or function parameters
 - Explicitly typing a variable type
 - Removing the explicitly type annotation from a variable
 - Removing useless spaces
 - Replacing single if statement with ternary conditionals
 - Renaming a function
 - Renaming a bot command function
 - Modify bot reply text (only the text)
 - Replacing string format function with Python f-string

This does not include:
 - Replacing multiple lines of code with a function
 - Removing instruction (if statement with ternary conditions excluded)
 - Replacing a multiline if with a switch/match case
 - Modifying/Removing imports


### Code changes
Which are changes that AFFECT the logic part of the application
Ex:
 - Removing useless instructions
 - Replacing line of codes with new/existing functions to simplify reading
 - Deleting old UNUSED functions
 - Deleting/Adding new bot messages (this does not include modifying existing ones if the only modified part is the message string)
 - Adding optional parameters to a function
 - Changing parameters order in a function call
 - Removing useless variables

It does not include:
 - Changing the logic sense of a function/line of code (Ex. changing a sum function to do a subtraction)
 - Fixes of bug (can include if small/irrelevant)
 - Adding new command/functions
 - Enhancing the functionality of existing functions

It is advisable (but not required) to create a commit for each of these sections and do not write explicitly what has changed in the description since all things are listed here, see this [refactor issue](https://github.com/users/zDany01/projects/10/views/1?pane=issue&itemId=71945500) for reference
