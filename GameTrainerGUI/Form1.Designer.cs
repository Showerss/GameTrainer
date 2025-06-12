//  this is where UI components are initialized, 
// Put all the .Location, .Size, .Text, and .Controls.Add(...) setup code here.


using System.Text;

namespace GameTrainerGUI;

partial class Form1
{
    ///  Required designer variable.
    private System.ComponentModel.IContainer components = null;

    // my character menus options
    private CheckBox playerGodMode, playerInfiniteStamina;
    private TrackBar playerSpeed, playerJumpHeight;

    //weapons menu options
    private CheckBox playerInfiniteAmmo, playerInfiniteGrenades;
    private TrackBar playerShootSpeed, playerRechargeSpeed;


    ///  Clean up any resources being used.
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


    ///  Required method for Designer support - do not modify
    ///  the contents of this method with the code editor.
    private void InitializeComponent()
    {

        this.components = new System.ComponentModel.Container();
        this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
        this.ClientSize = new System.Drawing.Size(800, 450);
        this.Text = "Form1";


        //godmode checkbox
        this.playerGodMode = new System.Windows.Forms.CheckBox();
        this.playerGodMode.AutoSize = true;
        this.playerGodMode.Location = new System.Drawing.Point(20,20);
        this.playerGodMode.Name = "playerGodMode";
        this.playerGodMode.Size = new System.Drawing.Size(200,17);
        this.playerGodMode.TabIndex = 0;
        this.playerGodMode.Text = "Enable GodMode";
        this.playerGodMode.UseVisualStyleBackColor = true;
        this.Controls.Add(this.playerGodMode);

    }

    #endregion
}
