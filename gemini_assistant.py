# -*- coding: utf-8 -*-
import uno
import unohelper
# Import the constant for setPosSize at the beginning
from com.sun.star.awt.PosSize import POS

try:
    # This import should work if you completed the 'pip install' step
    import google.generativeai as genai
except ImportError:
    genai = None

from com.sun.star.awt import XActionListener

# --- CONFIGURATION ---
API_KEY = "Your_API_key"
AI_MODEL = "gemini-2.5-flash" # Changed to a valid model name

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT_TEMPLATE = """
### Role:
You are my virtual assistant, acting in the role of an experienced and competent civil servant.
### Primary Goal:
Your main task is to provide me with professional assistance in working with texts, strictly adhering to my instructions.
### Key Behavioral Principles:
Tone of Communication: Always use a formal, business style. Your responses must be reserved, impersonal, logical, and factual.
### Ethics:
Act according to the ethics of a civil servant: be objective, impartial, accurate, and confidential. Avoid emotional judgments, personal opinions, and any information not relevant to the task.
### Execution of Instructions:
You must clearly and unconditionally follow my commands. DO NOT ask clarifying questions. DO NOT offer alternatives and DO NOT ask for confirmation. If my instruction is not sufficiently detailed, execute it based on generally accepted norms of business correspondence and previously provided context.
### Areas of Competence:
Your main responsibilities include:
Writing draft responses to letters and inquiries.
Composing official and business letters.
Structural analysis of documents, highlighting key theses.
Editing and improving the texts I provide to match a business style.
### Response Format:
Provide the response strictly on the substance of the request. Do not add greetings, farewells, or other accompanying text unless directly required by the task.

{user_instructions}
"""

# Global variables for accessing UNO services
CTX = uno.getComponentContext()
SM = CTX.getServiceManager()

def show_message_box(message, title="Message"):
    """Shows a native message box window."""
    try:
        desktop = SM.createInstanceWithContext("com.sun.star.frame.Desktop", CTX)
        frame = desktop.getActiveFrame()
        if not frame: return
        
        window = frame.getContainerWindow()
        toolkit = window.getToolkit()
        msgbox = toolkit.createMessageBox(window, "MESSAGEBOX", 1, title, str(message))
        msgbox.execute()
    except Exception:
        pass

class DialogHandler(unohelper.Base, XActionListener):
    """Class for creating and managing the native LibreOffice dialog."""

    def __init__(self, component):
        self.component = component
        self.dialog = self._create_dialog()

    def _create_dialog(self):
        """Programmatically creates and configures all dialog window elements."""
        dialog = SM.createInstanceWithContext("com.sun.star.awt.UnoControlDialog", CTX)
        dialog_model = SM.createInstanceWithContext("com.sun.star.awt.UnoControlDialogModel", CTX)

        # Properties for the dialog model itself
        dialog_model.Width = 320
        dialog_model.Height = 180
        dialog_model.Title = "AI Assistant"
        dialog.setModel(dialog_model)

        # Properties for the dialog window itself
        dialog.setPosSize(100, 100, 0, 0, POS)

        # 1. Label for the dropdown list
        action_label = dialog_model.createInstance("com.sun.star.awt.UnoControlFixedTextModel")
        action_label.PositionX = 10
        action_label.PositionY = 10
        action_label.Width = 300
        action_label.Height = 10
        action_label.Label = "1. Select an action (optional):"
        dialog_model.insertByName("ActionLabel", action_label)
        
        # 2. Dropdown list (ComboBox)
        action_selector_model = dialog_model.createInstance("com.sun.star.awt.UnoControlComboBoxModel")
        action_selector_model.PositionX = 10
        action_selector_model.PositionY = 25
        action_selector_model.Width = 300
        action_selector_model.Height = 15
        action_selector_model.Name = "ActionSelector" # New name
        action_selector_model.Dropdown = True
        # Add a blank element to the beginning
        action_selector_model.StringItemList = (
            "", # Blank default value
            "Improve text.",
            "What is this about?",
            "Make the text longer.",
            "Shorten the text."
        )
        action_selector_model.Text = "" # Set the default text to blank
        dialog_model.insertByName("ActionSelector", action_selector_model)
        
        # 3. Label for the text field
        prompt_label = dialog_model.createInstance("com.sun.star.awt.UnoControlFixedTextModel")
        prompt_label.PositionX = 10
        prompt_label.PositionY = 50
        prompt_label.Width = 300
        prompt_label.Height = 10
        prompt_label.Label = "2. Enter the main prompt or text:"
        dialog_model.insertByName("PromptLabel", prompt_label)

        # Bring back the multi-line text field
        text_field_model = dialog_model.createInstance("com.sun.star.awt.UnoControlEditModel")
        text_field_model.PositionX = 10
        text_field_model.PositionY = 65
        text_field_model.Width = 300
        text_field_model.Height = 70
        text_field_model.Name = "PromptInput" # New name
        text_field_model.MultiLine = True
        text_field_model.VScroll = True
        dialog_model.insertByName("PromptInput", text_field_model)

        # 4. OK Button
        ok_button_model = dialog_model.createInstance("com.sun.star.awt.UnoControlButtonModel")
        ok_button_model.PositionX = 200
        ok_button_model.PositionY = 150 # Changed position
        ok_button_model.Width = 50
        ok_button_model.Height = 14
        ok_button_model.Label = "OK"
        ok_button_model.PushButtonType = 0
        ok_button_model.DefaultButton = True
        dialog_model.insertByName("OkButton", ok_button_model)

        # 5. Cancel Button
        cancel_button_model = dialog_model.createInstance("com.sun.star.awt.UnoControlButtonModel")
        cancel_button_model.PositionX = 255
        cancel_button_model.PositionY = 150 # Changed position
        cancel_button_model.Width = 55
        cancel_button_model.Height = 14
        cancel_button_model.Label = "Cancel"
        cancel_button_model.PushButtonType = 2
        dialog_model.insertByName("CancelButton", cancel_button_model)
        
        # Assign the listener to the created control
        dialog.getControl("OkButton").addActionListener(self)
        
        self.dialog = dialog
        return self.dialog

    def show(self):
        """Shows the dialog box and returns the result."""
        self.dialog.setVisible(True)
        return self.dialog.execute()

    def actionPerformed(self, action_event):
        """This function executes when the OK button is clicked."""
        # --- NEW VALIDATION LOGIC ---
        # 1. Get text from BOTH fields
        action_text = self.dialog.getControl("ActionSelector").getText().strip()
        prompt_text = self.dialog.getControl("PromptInput").getText().strip()

        # 2. Check if BOTH fields are empty
        if not action_text and not prompt_text:
            show_message_box("Prompt cannot be empty. Please select an action or enter text.", "Error")
            return
            
        # 3. Combine the two fields into one final prompt
        if action_text and prompt_text:
            # If both values exist, combine them
            user_input = f"{action_text}: {prompt_text}"
        elif action_text:
            # If only the action from the list exists
            user_input = action_text
        else:
            # If only the text from the field exists
            user_input = prompt_text

        # --- The rest of the code remains unchanged ---
        
        # Robust logic for getting selected text
        selected_text = ""
        try:
            selection = self.component.getCurrentSelection()
            if hasattr(selection, 'supportsService') and selection.supportsService("com.sun.star.text.TextRanges") and len(selection) > 0:
                text_range = selection.getByIndex(0)
                selected_text = text_range.String
            elif hasattr(selection, 'String'):
                selected_text = selection.String
        except Exception:
            selected_text = ""
        
        instructions = f"Instructions:\n{user_input}"
        if selected_text:
            instructions += f"\n\nText to work on:\n{selected_text}"
        
        final_prompt = SYSTEM_PROMPT_TEMPLATE.format(user_instructions=instructions)
        
        self.dialog.endExecute()
        # show_message_box("Sending request to AI...", "Generating")

        try:
            genai.configure(api_key=API_KEY)
            ai_model = genai.GenerativeModel(AI_MODEL)
            response = ai_model.generate_content(final_prompt)
            
            # show_message_box(str(response), "Full response from API")
            
            generated_text = response.text
            
            current_selection = self.component.getCurrentSelection()
            range_to_write = current_selection.getByIndex(0) if hasattr(current_selection, 'getByIndex') else current_selection
            range_to_write.setString(generated_text)
            
        except Exception as e:
            show_message_box(f"Failed to generate text:\n{e}", "API Error")

def generate_text_with_ai():
    """Main trigger function for the macro."""
    if not genai:
        show_message_box("Library 'google-generativeai' not found. Please install it in the LibreOffice Python environment.", "Critical Error")
        return
        
    if not API_KEY or API_KEY == "Your_API_key":
        show_message_box("Please insert your Google AI API key into the script's code.", "Configuration Error")
        return

    desktop = SM.createInstanceWithContext("com.sun.star.frame.Desktop", CTX)
    model = desktop.getCurrentComponent()

    if not hasattr(model, "getCurrentSelection"):
        show_message_box("This script can only be run in a text document.", "Error")
        return
        
    handler = DialogHandler(model)
    handler.show()

# Export the function so LibreOffice can call it
g_exportedScripts = (generate_text_with_ai,)
