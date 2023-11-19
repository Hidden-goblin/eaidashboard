# Headers received

- `eaid-next` contains the custom event to trigger after the action took place
- `eaid-request` contains the request's type of object 
    - FORM
    - TABLE
    - REDIRECT
    - MAIN

# Headers sent

- `hx-trigger` contains the custom event to trigger

# Modal usage

- Request the modal template and target to `#modals-here`
- In the modal do your stuff
  - Implement a "dismiss" action which `modalClear` event can trigger
- The update the updating endpoint so that it could return the header `HX-Trigger`

```python

def update_function(body, request):
    try:
        #  Check authorization
        if  not is_updatable(request, right_tuple):
            return templates.TemplateResponse("error_message.html",{
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again."
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        # Do the treatment here
        
        # Success
        return templates.TemplateResponse("void.html",
                                          {"request": request},
                                          headers={"HX-Trigger": "modalClear",  # For multiple trigger use 
                                                    # json.dumps({"triggerone":"", "triggertwo": ""})
                                                   "HX-Trigger-After-Swap": "navRefresh"})
    except Exception as exception:
        log_error("\n".join(exception.args))
        return templates.TemplateResponse("forms/__.html",  # Recall the forms
                                          {
                                              "request": request,
                                              "name": body.name,  # Add data which may be recall
                                              "message": "\n".join(exception.args)  # Add the error message
                                          },
                                          headers={"HX-Retarget": "#modal",  # Retarget
                                                   "HX-Reswap": "beforeend"})   # Change swap
```

```html
<!-- There is still duplication -->
{% if name %}  <!-- May just be the presence of message -->
   <!-- This part is the error case -->
   <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Modal title</h5>
            </div>
            <div class="modal-body">
                <div class="container">
                    <form hx-patch="/front/v1/projects/{{}}/campaigns/{{version}}/{occurrence}}" <!-- The action -->
                          hx-ext='json-enc'
                          hx-headers='{"eaid-next": "modalClear"}' >
                        
                        <div class="mb-3" >
                            <!-- Add the form here for each field -->
                            <span class="text-danger" >
                                      {{message}}  <!-- The error message you want to display -->
                            </span>
                        </div>
                        <div id="modalErrorMessage" class="container show"></div>
                        <div class="button"> 
                            <button type="submit" class="btn btn-secondary">
                                Update
                            </button>
                        </div>
                    </form>
                </div>

            </div>
            <div class="modal-footer"> 
              <!-- The dismiss action -->
                <button type="button"
                        class="btn btn-secondary"
                        hx-delete="/clear"
                        hx-trigger="click, modalClear from:body"
                        hx-target="#modals-here"
                >Dismiss
                </button>
            </div>
        </div>
    </div>
{% else %}
<!-- Main form -->
<div id="modal-backdrop" class="modal-backdrop fade show" style="display:block;"></div>
<div id="modal" class="modal fade show" style="display:block;">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Modal title</h5>
            </div>
            <div class="modal-body">
                <div class="container">
                    <form hx-post="/front/v1/projects"
                          hx-ext='json-enc'
                          hx-headers='{"eaid-next": "modalClear"}'>
                        <div class="mb-3" >
                            <!-- Your form here -->
                        </div>
                        <div id="modalErrorMessage" class="container show"></div>
                        <div class="button">
                            <button type="submit" class="btn btn-secondary">
                                Create
                            </button>
                        </div>
                    </form>
                </div>

            </div>
            <div class="modal-footer">
                <button type="button"
                        class="btn btn-secondary"
                        hx-delete="/clear"
                        hx-trigger="click, modalClear from:body"
                        hx-target="#modals-here"
                >Dismiss
                </button>
            </div>
        </div>
    </div>
</div>
{% endif %}
```