# Front error message

## Template

Error message template is `error_message.html`.

## Parameters

- highlight: Text part you want to highlight to the end user
- sequel: Text part following the highlighted one you want to display to the end user
- advise: Text part containing advise to the end user in order to fix the error

## How-to

### Send an error message

Return a `error_message.html` template using the parameters.

Add to the header `{"HX-Retarget": "#messageBox"}` so that the error message will be displayed within the message box.