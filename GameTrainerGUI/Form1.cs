//  handling of logic, events and interactive events
// Handle event logic like trackBar1.ValueChanged or checkBox1.CheckedChanged

// Write custom methods or call C++ functions later

using System.Diagnostics.Eventing.Reader;
using System.Drawing.Text;
using System.Media;
using System.Windows.Forms;

namespace GameTrainerGUI;

public partial class Form1 : Form
{
    public Form1()
    {

        
        InitializeComponent();
        playerGodMode.CheckedChanged += CheckGodMode;

        this.components = new System.ComponentModel.Container();
        this.tabControl = new System.Windows.Forms.TabControl();
        this.tabCharacter = new System.Windows.Forms.TabPage("Character", this.tabControl);
        this.tabWeapons = new System.Windows.Forms.TabPage("Weapons", this.tabControl);
        this.tabItems = new System.Windows.Forms.TabPage("Items", this.tabControl);
        this.tabMemory = new System.Windows.Forms.TabPage("Memory", this.tabControl);    }

        private void CheckGodMode(object sender, EventArgs e)
        {
            if (playerGodMode.Checked)
            {
                //call c++ file for memory editing
            }
            else
            {
                MessageBox.Show("God mode disabled");
            }
        }
    }
}
