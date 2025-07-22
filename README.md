# 🤖 AI Assistant for LibreOffice Writer powered by Gemini

This script integrates the **Google Gemini API** into **LibreOffice Writer**, allowing you to edit and generate text directly within the document using a convenient dialog box.

-----

## ✨ Features

  * **Direct Gemini Integration:** Send requests to the AI without leaving the text editor.
  * **Works with Selected Text:** The script automatically detects your selected text and adds it to the request context.
  * **Prompt Templates:** Use the dropdown list with predefined commands ("Improve text," "Shorten text," etc.).
  * **Custom Prompts:** Enter your own detailed prompts in the text field.
  * **Convenient Launch:** Run the script using a toolbar button or a keyboard shortcut.

-----

## 📋 Requirements

  * **LibreOffice 7.0** or newer.
  * **Python 3.8+** (usually included with the LibreOffice installation).
  * **Google Gemini API Key.** You can get one for free at the [Google AI Studio](https://aistudio.google.com/app/apikey).

-----

## 🛠️ Installation and Setup

Follow these steps to set up the script.

### Step 1: Install the Google Library

This is the most important step. You need to install the `google-generativeai` Python library into the environment used by LibreOffice.

1.  **Find your LibreOffice `python.exe` file.**

      * **Windows:** `C:\Program Files\LibreOffice\program\python.exe`
      * **Linux:** `/usr/lib/libreoffice/program/python`

2.  **Open a terminal (command prompt) with administrator rights.**

      * **Windows:** Press `Win+X` and select "Terminal (Admin)" or "Windows PowerShell (Admin)".
      * **Linux:** Open a terminal and run the command with `sudo`.

3.  **Execute the installation command,** using the full path to `python.exe` in quotes:

    ```bash
    # Example for Windows
    "C:\Program Files\LibreOffice\program\python.exe" -m pip install google-generativeai

    # Example for Linux
    sudo /usr/lib/libreoffice/program/python -m pip install google-generativeai
    ```

### Step 2: Add the Script to LibreOffice

1.  Copy the entire code from the script.
2.  Open LibreOffice Writer.
3.  Go to the menu **Tools → Macros → Organize Macros → Python...**.
4.  On the left, select **My Macros → Standard**. If the `Standard` folder does not exist, create it.
5.  Click **New**, enter a name for the file (e.g., `gemini_assistant`), and click **OK**.
6.  A text editor will open. **Delete all existing code** and paste the code you copied.
7.  Save the file (`Ctrl+S`) and close the editor.

### Step 3: Configure the Script

1.  In the same macro editor, find the `CONFIGURATION` section at the beginning of the code.

2.  Replace `"Your_API_key"` with your **actual API key**.

3.  Ensure the `AI_MODEL` name is current.

    ```python
    # --- CONFIGURATION ---
    API_KEY = "YOUR-REAL-API-KEY-FROM-GOOGLE"
    AI_MODEL = "gemini-1.5-flash-latest"
    ```

### Step 4: Create a Toolbar Button (Recommended)

1.  Go to **Tools → Customize...** and open the **Toolbars** tab.
2.  Create a new toolbar (e.g., "AI Tools").
3.  Click **Add...** and in the **Category** list, select **LibreOffice Macros**.
4.  Find your script: `My Macros` → `Standard` → `gemini_assistant` → `generate_text_with_ai`.
5.  Add it, and then optionally, click **Modify** to choose a nice icon for the button.
6.  Click **OK** to save all changes.

-----

## 🚀 Usage

1.  Open a document in LibreOffice Writer.
2.  Select the text you want to edit (optional).
3.  Click the newly created button on your toolbar.
4.  In the dialog box that appears:
      * Select a predefined action from the dropdown list.
      * And/or enter your detailed prompt in the text field.
5.  Click **OK** or press the **Enter** key.
6.  Wait for the response. The selected text will be replaced with the result from Gemini.

-----

## ⚖️ License

This project is distributed under the MIT License. See the `LICENSE` file for more details.
