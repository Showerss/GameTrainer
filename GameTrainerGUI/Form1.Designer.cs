//  this is where UI components are initialized, 
// Put all the .Location, .Size, .Text, and .Controls.Add(...) setup code here.


namespace GameTrainerGUI;

partial class Form1
{
    ///  Required designer variable.
    private System.ComponentModel.IContainer components = null;
    private System.Windows.Forms.TabControl tabControl;
    private System.Windows.Forms.TabPage tabCharacter, tabWeapons, tabRescources, tabItems, tabMemory;

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




    #region Windows Form Designer 


    ///  Required method for Designer support - do not modify
    ///  the contents of this method with the code editor.
    private void InitializeComponent()
    {

        //tab names
        this.components = new System.ComponentModel.Container();
        this.tabControl = new TabControl();
        this.tabCharacter = new TabPage("Character");
        this.tabWeapons = new TabPage("Weapons");
        this.tabRescources = new TabPage("Resources");
        this.tabItems = new TabPage("Items");
        this.tabMemory = new TabPage("Memory");


        //tabControl
        this.tabControl.Dock = DockStyle.Fill;
        this.tabControl.TabPages.AddRange(new TabPage[] { this.tabCharacter, this.tabWeapons, this.tabRescources, this.tabItems, this.tabMemory });
        this.tabControl.Location = new Point(0, 0);
        this.tabControl.Name = "tabControl";
        this.tabControl.SelectedIndex = 0;
        this.tabControl.Size = new Size(800, 450);
        this.tabControl.TabIndex = 0;

        //Character Tab
        this.playerGodMode = new CheckBox {Text = "Enable GodMode"};
        this.playerInfiniteStamina = new CheckBox {Text = "Infinite Stamina"};
        this.playerSpeed = new TrackBar {Text = "Speed"};
        this.playerJumpHeight = new TrackBar {Text = "Jump Height"};
        tabCharacter.Controls.AddRange(new Control[] { this.playerGodMode, this.playerInfiniteStamina, this.playerSpeed, this.playerJumpHeight });

        //Weapons Tab
        this.playerInfiniteAmmo = new CheckBox {Text = "Infinite Ammo"};
        this.playerInfiniteGrenades = new CheckBox {Text = "Infinite Grenades"};
        this.playerShootSpeed = new TrackBar {Text = "Shoot Speed"};
        this.playerRechargeSpeed = new TrackBar {Text = "Recharge Speed"};
        tabWeapons.Controls.AddRange(new Control[] { this.playerInfiniteAmmo, this.playerInfiniteGrenades, this.playerShootSpeed, this.playerRechargeSpeed });


        //Overall window style
        this.components = new System.ComponentModel.Container();
        this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
        this.ClientSize = new System.Drawing.Size(800, 450);
        this.Text = "Form1";


        

    }

    #endregion
}
