//  handling of logic, events and interactive events
// Handle event logic like trackBar1.ValueChanged or checkBox1.CheckedChanged

// Write custom methods or call C++ functions later

using System.Diagnostics.Eventing.Reader;

namespace GameTrainerGUI;

public partial class Form1 : Form
{
    public Form1()
    {
        InitializeComponent();
        playerGodMode.CheckedChanged += CheckGodMode;
    }

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
