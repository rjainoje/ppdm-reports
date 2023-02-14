# Custom Tool for PowerProtect Data Manager reports

A simple script developed for Dell PowerProtect Data Manager to provide most common reports of backup environment.

This script makes a series of REST API calls to PPDM to gather backup activities, assets and compliance information and parse the output to excel sheet. 
I have developed this tool for several reasons, first, to be able to demonstrate how customers can leverage powerful REST API to automate various tasks and second, to be able to provide a guidance on how to develop custom reports.

If you are looking for most comprehensive report for PPDM environment, look at my other repo ppdm-at.

This is a v1.0.0 and, based on the feedback, I will invest more time in adding data, graphs and analytics to it.

## Getting Started

**Windows**
The exe is available in Windows Exe folder, download the exe and execute the same. If you are not comfortable running an exe, you can download ppdmrpt.py file and run the same.

```
ppdmrpt.exe -s <PPDM IP> -u <user> -p <pwd> -rd <report days>
```

OR

**Windows/Linux**

```
ppdmrpt.py -s <PPDM NAME / IP> -u <user> -p <pwd> -rd <report days>
```

This will generate an excel sheet in the same folder from where you executed the command.



## Author

* **Raghava Jainoje** - [rjainoje](https://github.com/rjainoje)


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details