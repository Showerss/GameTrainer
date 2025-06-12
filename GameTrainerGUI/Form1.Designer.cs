//  this is where UI components are initialized, 
// Put all the .Location, .Size, .Text, and .Controls.Add(...) setup code here.


namespace GameTrainerGUI;

partial class Form1
{
    /// <summary>
    ///  Required designer variable.
    /// </summary>
    private System.ComponentModel.IContainer components = null;
    private System.Windows.Forms.CheckBox checkboxGodMode;

    /// <summary>
    ///  Clean up any resources being used.
    /// </summary>
    /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
    protected override void Dispose(bool disposing)
    {
        if (disposing && (components != null))
        {
            components.Dispose();
        }
        base.Dispose(disposing);
    }

    #region Windows Form Designer generated code

    /// <summary>
    ///  Required method for Designer support - do not modify
    ///  the contents of this method with the code editor.
    /// </summary>
    private void InitializeComponent()
    {
        this.components = new System.ComponentModel.Container();
        this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
        this.ClientSize = new System.Drawing.Size(800, 450);
        this.Text = "Form1";


        //godmode checkbox
        this.checkboxGodMode = new System.Windows.Forms.CheckBox();
        this.checkboxGodMode.AutoSize = true;
        this.checkboxGodMode.Location = new System.Drawing.Point(20,20);
        this.checkboxGodMode.Name = "checkboxGodMode";
        this.checkboxGodMode.Size = new System.Drawing.Size(200,17);
        this.checkboxGodMode.TabIndex = 0;
        this.checkboxGodMode.Text = "Enable GodMode";
        this.checkboxGodMode.UseVisualStyleBackColor = true;
        this.Controls.Add(this.checkboxGodMode);

        //superspeed checkbox

    }

    #endregion
}
