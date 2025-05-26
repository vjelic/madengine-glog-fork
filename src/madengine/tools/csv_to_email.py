"""Module to send emails.

This module provides the functions to send emails.

Copyright (c) Advanced Micro Devices, Inc. All rights reserved.
"""

# built-in modules
import os

# third-party modules
import pandas as pd


def convert_csv_to_html(path: str):
    """Convert CSV files to HTML files.

    Args:
        path: The path to the directory containing the CSV files.
    """
    if not os.path.exists(path) or not os.path.isdir(path):
        print("The specified path does not exist or is not a directory.")
        return

    full_html_source = ""
    html_file_path = "./run_results.html"
    for filename in os.listdir(path):
        # Check if the file is a CSV file
        if filename.endswith(".csv"):
            file_path = os.path.join(path, filename)

            # Read the CSV file using pandas
            df = pd.read_csv(file_path)

            ## Convert DataFrame to HTML and save it
            # html_file_path = file_path.rsplit('.', 1)[0] + '.html'
            # df.to_html(html_file_path)
            html_source = df.to_html()

            # Add H2 header to html_source
            html_source = (
                "<h2> "
                + file_path.rsplit(".", 1)[0].split("/")[1]
                + " </h2> "
                + html_source
            )

            # Now add html_source to single file
            full_html_source += html_source

            print(f"Converted {filename} to HTML and saved as {html_file_path}")

    func = open(html_file_path, "w")
    func.write(full_html_source)
    func.close()


class ConvertCsvToEmail:
    def __init__(self, args):
        """Initialize the ConvertCsvToEmail object.

        Args:
            args: The command-line arguments.
        """
        self.args = args
        self.return_status = False

    def run(self):
        """Convert the CSV files to HTML files."""
        path = self.args.path
        convert_csv_to_html(path)

        self.return_status = True
        return self.return_status
