using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;
using System.Threading; 
using System.IO;
using System.Windows.Forms; 

using System.Windows.Automation;
using System.Linq.Expressions;
using static System.Windows.Forms.VisualStyles.VisualStyleElement.Window;
using System.Runtime.InteropServices;

namespace MPTSaveSpectrumLibrary

{
    /// <summary>
    /// Provides UI automation methods for launching and interacting with the Tec5.MPT.Shell spectroscopy application.
    /// </summary>
    public class SaveSpectrumUIHelper
    {

        /// <summary>
        /// Starts the spectroscopy program and waits until it is ready.
        /// </summary>
        /// <returns>True if the program is successfully started and ready; otherwise, false.</returns>
        // This method starts the program for Spectroscopy Measurments and will return PID of the program
        public static bool StartProgram()
        {
            try
            {
                while (IsProgramRunning("Tec5.MPT.Shell") is false)
                {
                    Process process = Process.Start("C:\\Program Files (x86)\\tec5\\tecSaaS MPT\\Tec5.MPT.Shell.exe");

                    //System.Threading.Thread.Sleep(2000);

                    if (process != null)
                    {
                        int pid = process.Id;
                        //return pid;
                        IsReady(pid);
                    }
                }

                Process[] processes = Process.GetProcessesByName("Tec5.MPT.Shell");

                ConnectDevice(processes[0].Id);

                //return processes[0].Id; 
                return IsReady(processes[0].Id);
            }
            catch (Exception ex)
            {
                Console.WriteLine("C# Exception Experienced: " + ex.ToString());
                return false; 
            }
        }

        /// <summary>
        /// Gets the process ID of the running spectroscopy program.
        /// </summary>
        /// <returns>The process ID of the spectroscopy program if found; otherwise, 0.</returns>
        public static int GetProgramId()
        {
            try
            {
                Process[] processes = Process.GetProcessesByName("Tec5.MPT.Shell");

                return processes[0].Id;
            }
            catch (Exception ex)
            {
                Console.WriteLine("C# Exception Experienced: " + ex.ToString());
                return 0; 
            }
        }

        /// <summary>
        /// Retrieves the main AutomationElement of the spectroscopy program based on its process ID.
        /// </summary>
        /// <param></param>
        /// <returns>name=parentElement</returns>
        public static AutomationElement GetProgramElement()
        {
            try
            {   
                int pid = GetProgramId();
                AutomationElement parentElement = AutomationElement.RootElement.FindFirst(
                    TreeScope.Children,
                    new PropertyCondition(AutomationElement.ProcessIdProperty, pid)
                    );

                if (parentElement == null)
                {
                    Console.WriteLine("Parent element not found.");
                    return null; 
                }
                return parentElement; 
            }
            catch (Exception ex) {
                Console.WriteLine("C# Exception Experienced: " + ex.ToString());
                return null; 
            }
        }

        /// <summary>
        /// Monitors the measurement process in the spectroscopy application.
        /// </summary>
        /// <param></param>
        public static void StartMonitoringMeasurement()
        {
            AutomationElement parentElement = GetProgramElement();

            // Start Measurement
            AutomationElement measurementMenu = parentElement.FindFirst(TreeScope.Descendants,
                new AndCondition(
                    new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.MenuItem),
                    new PropertyCondition(AutomationElement.NameProperty, "Measurement")
                    )
                ); 

            if (measurementMenu == null)
            {
                Console.WriteLine("Measurement menu not found.");
                return;
            }


            var supportedPatterns = measurementMenu.GetSupportedPatterns();
            foreach (var p in supportedPatterns)
            {
                Console.WriteLine("Supported pattern: " + p.ProgrammaticName);
            }


            if (measurementMenu.TryGetCurrentPattern(ExpandCollapsePattern.Pattern, out object expandObj))
            {
                var expandPattern = (ExpandCollapsePattern)expandObj;
                expandPattern.Expand();

                if (expandPattern.Current.ExpandCollapseState == ExpandCollapseState.Collapsed)
                {
                    expandPattern.Expand();
                    System.Threading.Thread.Sleep(2000); 
                }
            }
            else
            {
                Console.WriteLine("Non-Expandable Measurement Menu.");
            }

            AutomationElement startMeasurement = measurementMenu.FindFirst(TreeScope.Descendants,
                new AndCondition(
                    new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.MenuItem),
                    new PropertyCondition(AutomationElement.NameProperty, "Start Measurement")
                    )
                );

            if (startMeasurement == null)
            {
                Console.WriteLine("Start Measurement menu item not found.");
                return;  
            }

            if (startMeasurement.TryGetCurrentPattern(InvokePattern.Pattern, out object startMeasurementObj))
            {
                var startMeasurementPattern = (InvokePattern)startMeasurementObj;
                startMeasurementPattern.Invoke();

                Console.WriteLine("Started Measurement Invoked"); 

            }
            else
            {
                Console.WriteLine("Start Measurement Not Found");
            }

           
            // Start Monitoring Button 
            var buttons = parentElement.FindAll(TreeScope.Descendants,
                new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Button));

            foreach (AutomationElement button in buttons)
            {

                var descendants = button.FindAll(TreeScope.Descendants,
                    Condition.TrueCondition);

                foreach (AutomationElement child in descendants)
                {
                    string name = child.Current.Name;
                    if (name == "Start Monitor")
                    {

                        // Found the matching button!
                        Console.WriteLine("Found button with matching child.");

                        if (button.TryGetCurrentPattern(InvokePattern.Pattern, out object invokePatternObj))
                        {
                            var invokePattern = (InvokePattern)invokePatternObj;
                            invokePattern.Invoke();
                            Console.WriteLine("Button invoked.");
                        }
                        else
                        {
                            Console.WriteLine("Button is not invokable.");
                        }

                        return;
                    }
                }
            }

        }

        /// <summary>
        /// This method will stop monitoring then measurement.
        /// </summary>
        public static void StopMonitoringMeasurement()
        {
            AutomationElement parentElement = GetProgramElement();

            // Start Measurement
            AutomationElement measurementMenu = parentElement.FindFirst(TreeScope.Descendants,
                new AndCondition(
                    new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.MenuItem),
                    new PropertyCondition(AutomationElement.NameProperty, "Measurement")
                    )
                );

            if (measurementMenu == null)
            {
                Console.WriteLine("Measurement menu not found.");
                return;
            }


            var supportedPatterns = measurementMenu.GetSupportedPatterns();
            foreach (var p in supportedPatterns)
            {
                Console.WriteLine("Supported pattern: " + p.ProgrammaticName);
            }


            if (measurementMenu.TryGetCurrentPattern(ExpandCollapsePattern.Pattern, out object expandObj))
            {
                var expandPattern = (ExpandCollapsePattern)expandObj;
                expandPattern.Expand();

                if (expandPattern.Current.ExpandCollapseState == ExpandCollapseState.Collapsed)
                {
                    expandPattern.Expand();
                    System.Threading.Thread.Sleep(500);
                }
            }
            else
            {
                Console.WriteLine("Non-Expandable Measurement Menu.");
            }

            AutomationElement stopMeasurement = measurementMenu.FindFirst(TreeScope.Descendants,
                new AndCondition(
                    new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.MenuItem),
                    new PropertyCondition(AutomationElement.NameProperty, "Stop Measurement")
                    )
                );

            if (stopMeasurement == null)
            {
                Console.WriteLine("Start Measurement menu item not found.");
                return;
            }

            if (stopMeasurement.TryGetCurrentPattern(InvokePattern.Pattern, out object stopMeasurementObj))
            {
                var stopMeasurementPattern = (InvokePattern)stopMeasurementObj;
                stopMeasurementPattern.Invoke();

                Console.WriteLine("Started Measurement Invoked");

            }
            else
            {
                Console.WriteLine("Start Measurement Not Found");
            }


            // Start Monitoring Button 
            var buttons = parentElement.FindAll(TreeScope.Descendants,
                new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Button));

            foreach (AutomationElement button in buttons)
            {

                var descendants = button.FindAll(TreeScope.Descendants,
                    Condition.TrueCondition);

                foreach (AutomationElement child in descendants)
                {
                    string name = child.Current.Name;
                    if (name == "Stop Monitor")
                    {

                        // Found the matching button!
                        Console.WriteLine("Found button with matching child.");

                        if (button.TryGetCurrentPattern(InvokePattern.Pattern, out object invokePatternObj))
                        {
                            var invokePattern = (InvokePattern)invokePatternObj;
                            invokePattern.Invoke();
                            Console.WriteLine("Button invoked.");
                        }
                        else
                        {
                            Console.WriteLine("Button is not invokable.");
                        }

                        return;
                    }
                }
            }

        }


        /// <summary>
        /// Terminates the spectroscopy program and restarts it after a short delay.
        /// </summary>
        public static void RestartProgram()
        {
            Process[] processes = Process.GetProcessesByName("Tec5.MPT.Shell");
            processes[0].Kill();

            Thread.Sleep(2000);

        }

        /// <summary>
        /// Attempts to find and interact with the login window of the spectroscopy program using the given password.
        /// </summary>
        /// <param name="password">The password to input in the login dialog.</param>
        /// <returns>True if login was successful or not needed; otherwise, false.</returns>
        public static bool FindLoginWindow(string password)
        {

            try
            {

                Process[] processes = Process.GetProcessesByName("Tec5.MPT.Shell");

                int parentElementId = processes[0].Id;

                AutomationElement parentElement = AutomationElement.RootElement.FindFirst(
                    TreeScope.Children,
                    new PropertyCondition(AutomationElement.ProcessIdProperty, parentElementId)
                    );

                if (parentElement == null)
                    return false;

                AutomationElement childElement = parentElement.FindFirst(
                    TreeScope.Descendants,
                    new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Window)
                    );

                if (childElement == null) return LoggedIn(parentElement);

                AutomationElement passwordBox = childElement.FindFirst(
                    TreeScope.Descendants,
                    new PropertyCondition(AutomationElement.AutomationIdProperty, "PasswordBox")
                    );

                if (passwordBox == null) return LoggedIn(parentElement);

                if (passwordBox.TryGetCurrentPattern(ValuePattern.Pattern, out object pattern_01))
                {
                    ValuePattern valuePattern = (ValuePattern)pattern_01;
                    valuePattern.SetValue(password);

                }
                else return false;

                AutomationElement loginButton = childElement.FindFirst(
                    TreeScope.Descendants,
                    new PropertyCondition(AutomationElement.AutomationIdProperty, "LoginButton")
                    );
                if (loginButton == null) return LoggedIn(parentElement);

                if (loginButton.TryGetCurrentPattern(InvokePattern.Pattern, out object pattern_02))
                {
                    ((InvokePattern)pattern_02).Invoke();
                }
                else return false;

                return true; 
            }

            catch (Exception ex)
            {
                Console.WriteLine("C# Exception Experienced: " + ex.ToString());
                return false;
            }
        }

        /// <summary>
        /// Determines whether the application's UI is ready for user interaction.
        /// </summary>
        /// <param name="parentElementId">The process ID of the application's main window.</param>
        /// <returns>True if the application is ready; otherwise, false.</returns>
        public static bool IsReady(int parentElementId)
        {
            try
            {
                AutomationElement parentElement = AutomationElement.RootElement.FindFirst(
                     TreeScope.Children,
                     new PropertyCondition(AutomationElement.ProcessIdProperty, parentElementId)
                 );

                string windowName = parentElement.Current.Name;

                ;

                if (windowName.Contains("Offline"))
                {
                    return false;
                }
                else
                {
                    if (FindLoginWindow("user") == false) return false; 
                    return true;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine("C# Exception Experienced: " + ex.ToString());
                return false; 
            }
        }

        /// <summary>
        /// Checks if a user is logged in by detecting a Logout menu item.
        /// </summary>
        /// <param name="parentElement">The main AutomationElement representing the application window.</param>
        /// <returns>True if the user is logged in; otherwise, false.</returns>
        public static bool LoggedIn(AutomationElement parentElement)
        {
            try
            {
                AutomationElement logoutMenuItem = parentElement.FindFirst(
                    TreeScope.Descendants,
                    new AndCondition(
                        new PropertyCondition(AutomationElement.NameProperty, "Logout"),
                        new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.MenuItem),
                        new PropertyCondition(AutomationElement.IsEnabledProperty, true)
                        )
                    );

                if (logoutMenuItem == null) return false;

                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine("C# Exception Experienced: " + ex.ToString());
                return false;
            }
        }

        /// <summary>
        /// Connects the application to a spectroscopy device if not already connected.
        /// </summary>
        /// <param name="parentElementId">The process ID of the application's main window.</param>
        public static void ConnectDevice(int parentElementId)
        {
            if (IsReady(parentElementId) == true)
                {
                return; 
            }

            AutomationElement parentElement = AutomationElement.RootElement.FindFirst(
                 TreeScope.Children,
                 new PropertyCondition(AutomationElement.ProcessIdProperty, parentElementId)
             );

            if (parentElement == null)
                throw new Exception("Main application window not found.");

            ClickConnectButton(parentElement);

            //SendKeys.SendWait("{Enter}");
            ConnectToDeviceWindow(parentElement); 
            Thread.Sleep(4000);

            ConnectionContinue(parentElement); 
            //SendKeys.SendWait("{Enter}");
            Thread.Sleep(100);

            FindLoginWindow("user");
            Thread.Sleep(100);
            //SendKeys.SendWait("{Enter}");

            StartMonitoringMeasurement();
            Thread.Sleep(1000); 
        }

        /// <summary>
        /// Identifies and clicks the Connect button inside the "Connect - tecSaaS" dialog window.
        /// </summary>
        /// <param name="parentElement">The main AutomationElement of the application.</param>
        public static void ConnectToDeviceWindow(AutomationElement parentElement)
        {
            AutomationElementCollection connectWindows = parentElement.FindAll(
                TreeScope.Children,
                new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Window)
                );

            AutomationElement connectWindow = null; 
            foreach (AutomationElement possibleWindow in connectWindows)
            {
                if (possibleWindow.Current.Name.Contains("Connect - tecSaaS"))
                {
                    connectWindow = possibleWindow;
                    break; 
                }
            }

            if (connectWindow == null)
            {
                throw new Exception("Connect - tecSaas Window not found"); 
            }

            AutomationElement connectButton = connectWindow.FindFirst(
                TreeScope.Descendants,
                new AndCondition(
                    new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Button),
                    new PropertyCondition(AutomationElement.NameProperty, "Connect"))
                ); 

            if (connectButton == null)
            {
                throw new Exception("Cannot find the connectButton"); 
            }
            
            try
            {
                if (connectButton.TryGetCurrentPattern(InvokePattern.Pattern, out object patternObj))
                {
                    ((InvokePattern)patternObj).Invoke();
                    Console.WriteLine("Connect Button clicked.");
                }
            }
            catch (Exception ex) {
                Console.WriteLine("C# Exception Experienced: " + ex.ToString());
            }

        }

        /// <summary>
        /// Closes the connection confirmation dialog if it appears.
        /// </summary>
        /// <param name="parentElement">The main AutomationElement of the application.</param>
        public static void ConnectionContinue(AutomationElement parentElement)
        {

            AutomationElement connectionInfoWindow = null;
            //AutomationElement connectionInfoWindows = null; 

            int retries = 20;
            int delayMs = 500;

            for (int i = 0; i < retries; i++)
            {
                AutomationElementCollection connectionInfoWindows = parentElement.FindAll(
                TreeScope.Children,
                new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Window));

                foreach (AutomationElement window in connectionInfoWindows)
                {
                    try
                    {
                        if (!string.IsNullOrEmpty(window.Current.Name) &&
                        window.Current.Name.Contains("Connection established"))
                        {
                            connectionInfoWindow = window;
                            break;
                        }
                    }
                    catch (ElementNotAvailableException)
                    {
                        continue; // The windows closed before it could be accessed. 
                    }
                }

                if (connectionInfoWindow != null)
                    break;

                Thread.Sleep(delayMs);
            }

            //foreach (AutomationElement window in connectionInfoWindows)
            //{
                    
            //    if (window.Current.Name.Contains("Connection established"))
            //    {
            //        connectionInfoWindow = window;
            //        break;
            //    }
            //    else
            //    {
            //        //AutomationElement connectionInfoWindow = null;
            //    }
            //}
            //if (connectionInfoWindows == null)
            //{
            //    throw new Exception("Cannot find window: 'Connection Estabilished'"); 
            //}

            object pattern;
            if (connectionInfoWindow.TryGetCurrentPattern(WindowPattern.Pattern, out pattern))
            {
                ((WindowPattern)pattern).Close();
                Console.WriteLine("Window closed successfully.");
            }




        }

        /// <summary>
        /// Clicks the appropriate Connect button located within the toolbar of the main application.
        /// </summary>
        /// <param name="parentElement">The main AutomationElement of the application.</param>
        public static void ClickConnectButton(AutomationElement parentElement)
        {
            // This class will connect the host computer to the diode array 

            AutomationElement toolbar = parentElement.FindFirst(
            TreeScope.Descendants,
            new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.ToolBar));

            if (toolbar == null)
            {
                Console.WriteLine("Toolbar not found.");
                return;
            }

            // Find all buttons inside the toolbar
            AutomationElementCollection buttons = toolbar.FindAll(
                TreeScope.Children,
                new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Button));

            if (buttons.Count > 1)
            {
                AutomationElement button = buttons[1]; // Get the desired button

                Console.WriteLine($"Found button {1 + 1} in toolbar.");

                // Try clicking it using InvokePattern
                if (button.TryGetCurrentPattern(InvokePattern.Pattern, out object patternObj))
                {
                    ((InvokePattern)patternObj).Invoke();
                    Console.WriteLine("Button clicked.");
                }
                else
                {
                    Console.WriteLine("Button does not support InvokePattern.");
                }
            }
            else
            {
                Console.WriteLine($"Button index {1} out of range. Found {buttons.Count} buttons.");
            }
        }

        /// <summary>
        /// Determines whether a program with the specified name is currently running and ensures only one instance remains.
        /// </summary>
        /// <param name="applicationName">The name of the application process (e.g., "Tec5.MPT.Shell").</param>
        /// <returns>True if the application is running; otherwise, false.</returns>
        public static bool IsProgramRunning(string applicationName)
        {
            Process[] processes = Process.GetProcessesByName(applicationName);
            int iter = 0; 

            if (processes.Length == 0)
            {
                return false; 
            }
            else
            {
                if (processes.Length > 1)
                {
               
                    foreach (Process process in processes)
                    {
                        if (iter > 0)
                        {
                            try
                            {
                                process.Kill();
                            }
                            catch (Exception ex)
                            {
                                Console.WriteLine("C# Exception Experienced: " + ex.ToString());
                                break;
                                // Console.WriteLine($"Error Closing process: {ex.Message}");
                            }
                        }
                        iter++; 
                        
                    }
                     
                }
            }

            return true; 
        }

        /// <summary>
        /// Clicks a UI control element based on a specified property name and value within a window.
        /// </summary>
        /// <param name="parentElementId">The process ID of the application's main window.</param>
        /// <param name="propertyName">The name of the property to match (e.g., "name", "classname", "automationid").</param>
        /// <param name="propertyValue">The value of the property to look for.</param>
        // This method performs a button click based on the window title and button name.
        public static void ClickControl(int parentElementId, string propertyName, string propertyValue)
        {
            // Find the parent element (e.g., main window) using its name
            AutomationElement parentElement = AutomationElement.RootElement.FindFirst(
                TreeScope.Children,
                new PropertyCondition(AutomationElement.ProcessIdProperty, parentElementId)
            );

            if (parentElement == null)
                throw new Exception("Parent element not found."); // Parent element (e.g., window) not found

            // Choose the property to search for the control
            AutomationProperty propertyToSearch;

            switch (propertyName.ToLower())
            {
                case "name":
                    propertyToSearch = AutomationElement.NameProperty;
                    break;
                case "classname":
                    propertyToSearch = AutomationElement.ClassNameProperty;
                    break;
                case "controltype":
                    propertyToSearch = AutomationElement.ControlTypeProperty;
                    break;
                case "automationid":
                    propertyToSearch = AutomationElement.AutomationIdProperty;
                    break;
                default:
                    throw new Exception("Unsupported property type."); // Throw an error for unsupported properties
            }

            // Search for the control inside the parent element
            AutomationElement control = parentElement.FindFirst(
                TreeScope.Descendants, // Search recursively within the parent element
                new PropertyCondition(propertyToSearch, propertyValue) // Match the specified property and value
            );

            // Check if the control supports the InvokePattern (used for clickable elements)
            if (control != null && control.TryGetCurrentPattern(InvokePattern.Pattern, out object pattern))
            {
                // Invoke the control's action
                ((InvokePattern)pattern).Invoke();
                Console.WriteLine("Control clicked successfully.");
            }
            else
            {
                throw new Exception("Control not found or does not support InvokePattern.");
            }
        }

        /// <summary>
        /// Finds the "Save As" dialog that is a child of the application's main window.
        /// </summary>
        /// <param name="parentElement">The main AutomationElement representing the application's window.</param>
        /// <returns>The AutomationElement for the Save As dialog if found; otherwise, null.</returns>
        public static AutomationElement FindSaveAsDialog(AutomationElement parentElement)
        {
            // Find the Save As dialog (child of the main window)
            AutomationElement saveAsDialog = parentElement.FindFirst(
                TreeScope.Children,
                new AndCondition(
                    new PropertyCondition(AutomationElement.NameProperty, "Save As"), 
                    new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.LookupById(50032))
                    )
            );
                                    


            //if (saveAsDialog == null)
            //    throw new Exception("Save As dialog not found.");

            return saveAsDialog; 
        }

        /// <summary>
        /// Fills out the Save As dialog with the desired file name and file type selection.
        /// </summary>
        /// <param name="parentWindowId">The process ID of the application's main window.</param>
        /// <param name="fileName">The full file path where the file should be saved.</param>
        /// <param name="dialogTitle">Optional title of the Save As dialog. Defaults to "Save As".</param>
        public static void FillSaveAsDialog(int parentWindowId, string fileName, string dialogTitle = "Save As")
        {
            int index = -1;
            int totalTime = 100;
            int incTime = 50;
            int elapsedTime = 0;

            try
            {
                // Find the main application window
                AutomationElement parentWindow = AutomationElement.RootElement.FindFirst(
                    TreeScope.Children,
                    new PropertyCondition(AutomationElement.ProcessIdProperty, parentWindowId)
                );

                if (parentWindow == null)
                    throw new Exception("Main application window not found.");

                try
                {
                    ClickControl(parentWindowId, "automationid", "ExportButton");
                }

                catch (Exception ex)
                {
                    Console.WriteLine("Cannot Find Save As Button");
                    //Console.WriteLine("C# Exception: " + ex.ToString());
                    Console.WriteLine("C# Exception Experienced: " + ex.ToString());
                    CloseSaveAsDialogs(); 


                }

                //// Find the Save As dialog (child of the main window)
                //AutomationElement saveAsDialog = parentWindow.FindFirst(
                //    TreeScope.Children,
                //    new PropertyCondition(AutomationElement.NameProperty, dialogTitle)
                //);

                //if (saveAsDialog == null)
                //    throw new Exception("Save As dialog not found.");


                AutomationElement saveAsDialog = FindSaveAsDialog(parentWindow);
                

                while (elapsedTime < totalTime)
                {
                    saveAsDialog = FindSaveAsDialog(parentWindow);

                    if (saveAsDialog != null)
                    {
                        break;
                    }

                    Thread.Sleep(incTime);
                    int elaspedTime = elapsedTime + incTime;

                }
                if (saveAsDialog == null)
                {
                    throw new Exception("Save As Dialog not found");
                }

                // Find the file name input box within the Save As dialog
                AutomationElement fileNameBox = saveAsDialog.FindFirst(
                    TreeScope.Descendants,
                    new AndCondition(
                        //new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Edit), 
                        new PropertyCondition(AutomationElement.NameProperty, "File name:"),
                        new PropertyCondition(AutomationElement.LocalizedControlTypeProperty, "edit"),
                        new PropertyCondition(AutomationElement.AutomationIdProperty, "1148")
                                    //new PropertyCondition(AutomationElement.IsValuePatternAvailableProperty, true) 
                                    ));

                if (fileNameBox == null)
                    throw new Exception("File name input box not found.");

                Thread.Sleep(10);

                //Console.WriteLine(fileNameBox.GetCurrentPropertyValue(AutomationElement.NameProperty)); 

                // Set the file name in the input box
                ValuePattern valuePattern = fileNameBox.GetCurrentPattern(ValuePattern.Pattern) as ValuePattern;

                if (valuePattern != null)
                {
                    string fileDir = Path.GetDirectoryName(fileName);
                    string file = Path.GetFileName(fileName);

                    valuePattern.SetValue(Path.Combine(fileDir, file));
                }
                else
                {
                    throw new Exception("Unable to set file name in input box.");
                }


                // Locate the ComboBox
                AutomationElement comboBox = saveAsDialog.FindFirst(
                    TreeScope.Descendants,
                    new AndCondition(
                        new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.ComboBox),
                        new PropertyCondition(AutomationElement.NameProperty, "Save as type:")
                                    )
                    );
                if (comboBox == null)
                    throw new Exception("ComboBox not found.");

                comboBox.SetFocus();

                //System.Threading.Thread.Sleep(20);


                AutomationElementCollection listItems = comboBox.FindAll(
                   TreeScope.Descendants,
                   new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.ListItem)
                );

                index = listItems.Count - 1;
                //if (listItems.Count > index)
                //{
                AutomationElement listItem = listItems[index];

                // Try to get the SelectionItemPattern for the item
                if (listItem.TryGetCurrentPattern(SelectionItemPattern.Pattern, out object selectionPatternObj))
                {
                    SelectionItemPattern selectionItemPattern = (SelectionItemPattern)selectionPatternObj;

                    // Select the item
                    selectionItemPattern.Select();
                    //Console.WriteLine($"Selected item at index {index}: {listItem.Current.Name}");
                }
                else
                {
                    throw new Exception("The list item does not support SelectionItemPattern.");
                }
                //}
                //else
                //{
                //    throw new Exception("Index is out of range.");
                //}
                //// Expand the ComboBox
                //if (comboBox.TryGetCurrentPattern(ExpandCollapsePattern.Pattern, out object expandCollapsePatternObj))
                //{
                //    var expandCollapsePattern = (ExpandCollapsePattern)expandCollapsePatternObj;
                //    expandCollapsePattern.Expand();

                //    // Wait for the ComboBox to expand (if needed)
                //    //System.Threading.Thread.Sleep(20);

                //    // Find the desired item in the ComboBox dropdown
                //    AutomationElement comboBoxItem = comboBox.FindFirst(
                //        TreeScope.Descendants,
                //        new PropertyCondition(AutomationElement.NameProperty, "ASCII (*.txt)")
                //    );

                //    if (comboBoxItem == null)
                //        throw new Exception($"ComboBox item 'ASCII (*.txt)' not found.");

                //    // Select the desired item
                //    if (comboBoxItem.TryGetCurrentPattern(SelectionItemPattern.Pattern, out object selectionItemPatternObj))
                //    {
                //        var selectionItemPattern = (SelectionItemPattern)selectionItemPatternObj;
                //        selectionItemPattern.Select();
                //        Console.WriteLine($"ComboBox value changed to 'ASCII (*.txt)'.");
                //    }
                //    else
                //    {
                //        throw new Exception("Unable to select the ComboBox item.");
                //    }
                //}
                //else
                //{
                //    throw new Exception("ComboBox does not support ExpandCollapsePattern.");
                //}

                // Find the Save button within the Save As dialog
                AutomationElement saveButton = saveAsDialog.FindFirst(
                        TreeScope.Children,
                        new AndCondition(
                            new PropertyCondition(AutomationElement.NameProperty, "Save"),
                            new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Button)
                            )
                    );

                if (saveButton == null)
                    throw new Exception("Save button not found.");

                try
                {
                    if (saveButton.TryGetCurrentPattern(InvokePattern.Pattern, out object pattern_save))
                    {
                        ((InvokePattern)pattern_save).Invoke();
                        Console.WriteLine("File saved successfully.");

                    }
                }
                catch
                {
                    var windowPattern = saveAsDialog.GetCurrentPattern(WindowPattern.Pattern) as WindowPattern;
                    windowPattern.Close(); // Close the window forcefully

                    Console.WriteLine("Save Button not pressed");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine("C# Exception: " + ex.ToString());
            }
        }

        /// <summary>
        /// Gets the process ID of the first instance of a process with the specified name.
        /// </summary>
        /// <param name="processName">The name of the process to search for.</param>
        /// <returns>The process ID if found; otherwise, -1.</returns>
        public static int GetProcessIdByName(string processName)
        {
            try
            {
                Process[] processes = Process.GetProcessesByName(processName); // Get all processes with the given name

                if (processes.Length > 0)
                {
                    // Assuming the first instance is the one you're interested in
                    return processes[0].Id; // Return the PID of the first instance
                }
                else
                {
                    Console.WriteLine($"No process found with name: {processName}");
                    return -1; // Return -1 if no process found
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
                return -1;
            }
        }

        /// <summary>
        /// Forces the .NET garbage collector to run immediately and clean up finalized objects.
        /// Use this in long-running processes or when interop memory pressure is a concern.
        /// </summary>
        public static void ForceGC()
        {
            GC.Collect();
            GC.WaitForPendingFinalizers();
        }

        /// <summary>
        /// Closes all open "Save As" dialog windows on the desktop by locating them through UI Automation
        /// and invoking their close buttons.
        /// </summary>
        /// <remarks>
        /// This method uses UI Automation to find top-level windows with the name "Save As" and attempts to
        /// invoke the "Close" button on each of them, effectively closing the dialogs if they are found.
        /// </remarks>
        /// <exception cref="InvalidCastException">
        /// Thrown if the close button exists but does not support the <see cref="InvokePattern"/> pattern.
        /// </exception>
        public static void CloseSaveAsDialogs()
        {
            var windows = AutomationElement.RootElement.FindAll(TreeScope.Children,
                new PropertyCondition(AutomationElement.NameProperty, "Save As"));

            foreach (AutomationElement win in windows)
            {
                var closeButton = win.FindFirst(TreeScope.Descendants,
                new PropertyCondition(AutomationElement.AutomationIdProperty, "Close"));

                if (closeButton != null && closeButton.TryGetCurrentPattern(InvokePattern.Pattern, out var pattern))
                {
                    ((InvokePattern)pattern).Invoke();
                }
            }
        }

        /// <summary>
        /// Determines whether the macro is operating in a healthy state by checking
        /// the number of open "Save As" dialog windows.
        /// </summary>
        /// <returns>
        /// <c>true</c> if one or no "Save As" windows are open; otherwise, <c>false</c>.
        /// </returns>
        /// <remarks>
        /// This method queries the top-level windows and counts how many have the name "Save As".
        /// If more than one such window is open, it is assumed the macro may be malfunctioning
        /// (e.g., repeatedly triggering the "Save As" dialog).
        /// </remarks>
        public static bool IsMacroHealthy()
        {
            // Count open Save As dialogs
            var windows = AutomationElement.RootElement.FindAll(TreeScope.Children,
                new PropertyCondition(AutomationElement.NameProperty, "Save As"));

            return windows.Count <= 1;
        }
    }

    /// <summary>
    /// Provides helper methods to forcefully close windows based on their title, associated process ID (PID),
    /// or known UI patterns such as Save As dialogs. Useful for recovering from UI automation deadlocks or leaks.
    /// </summary>
    public static class WindowForceCloser
    {
        private const uint WM_CLOSE = 0x0010;

        [DllImport("user32.dll", SetLastError = true)]
        private static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);

        [DllImport("user32.dll")]
        private static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

        [DllImport("user32.dll")]
        private static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

        [DllImport("user32.dll")]
        private static extern bool IsWindowVisible(IntPtr hWnd);

        [DllImport("user32.dll")]
        private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

        private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

        /// <summary>
        /// Attempts to find and force-close a window titled "Save As" using the WM_CLOSE message.
        /// This is useful in UI automation recovery when Save As dialogs become unresponsive or multiply unexpectedly.
        /// </summary>
        public static void ForceCloseSaveAsDialogs()
        {
            IntPtr hwnd = FindWindow(null, "Save As");
            if (hwnd != IntPtr.Zero)
            {
                Console.WriteLine("Found Save As window. Sending WM_CLOSE...");
                PostMessage(hwnd, WM_CLOSE, IntPtr.Zero, IntPtr.Zero);
            }
            else
            {
                Console.WriteLine("Success: No Save As window found to CLOSE.");
            }
        }

        /// <summary>
        /// Forcefully closes all top-level windows belonging to the specified process ID (PID).
        /// Useful for terminating dialog boxes or application windows created by a specific process.
        /// </summary>
        /// <param name="pid">The PID of the process whose windows should be closed.</param>
        public static void ForceCloseWindowsByPid(int pid)
        {
            var handles = GetTopLevelWindowsForPid(pid);

            foreach (var hWnd in handles)
            {
                if (IsWindowVisible(hWnd))
                {
                    PostMessage(hWnd, WM_CLOSE, IntPtr.Zero, IntPtr.Zero);
                    Console.WriteLine($"[PID Window Close] Sent WM_CLOSE to hWnd {hWnd}");
                }
            }

            if (handles.Count == 0)
            {
                Console.WriteLine($"[PID Window Close] No top-level windows found for PID {pid}");
            }
        }

        /// <summary>
        /// Enumerates all top-level windows for a specific process ID.
        /// </summary>
        /// <param name="pid">The PID of the process.</param>
        /// <returns>List of window handles belonging to the process.</returns>
        private static List<IntPtr> GetTopLevelWindowsForPid(int pid)
        {
            List<IntPtr> handles = new List<IntPtr>();

            EnumWindows((hWnd, lParam) =>
            {
                GetWindowThreadProcessId(hWnd, out uint windowPid);
                if (windowPid == pid)
                {
                    handles.Add(hWnd);
                }
                return true;
            }, IntPtr.Zero);

            return handles;
        }
    }
}
