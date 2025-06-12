// Basic resizable GUI window in C# using Windows Forms

using System;
using System.Drawing;
using System.Windows.Forms;

namespace GameTrainerGUI
{
    public class MainWindow : Form
    {
        public MainWindow()
        {
            this.Text = "Game Trainer Base Window";
            this.Size = new Size(800, 600);
            this.MinimumSize = new Size(400, 300);
            this.FormBorderStyle = FormBorderStyle.Sizable;
            this.StartPosition = FormStartPosition.CenterScreen;
            this.BackColor = Color.FromArgb(30, 30, 30);
        }

        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainWindow());
        }
    }
}