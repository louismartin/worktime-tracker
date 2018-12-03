-- From: https://stackoverflow.com/questions/53132824/how-to-get-the-current-workspace-programmatically-on-macos/53396510?noredirect=1#comment93748931_53396510
set delimOrgs to text item delimiters
set text item delimiters to {"/"}
tell application "System Events" to set BGpict to ¬
     last text item of (picture of current desktop as text)
set text item delimiters to delimOrgs
return BGpict 
