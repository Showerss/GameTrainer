// Basic resizable GUI window in C# using Windows Forms
// program.cs launches form1, so we don't need to edit this muuch

namespace GameTrainerGUI
{
    public class MainWindow : Form
    {

        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new Form1());
        }
    }
}