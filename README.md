# Django Working Time Dashboard

<img src="./img/dashboard.png" width="800">

Django app for analysing and visualizing the time events tracked in Toggl. The app queries your recorded working time from the Toggl API and calculates your target and actual working time together with the stored non-working days and working hours per day.

## Built With

* Django 

### Installation

1. Clone the repo 
      ```sh
      git clone https://github.com/your_username_/Project-Name.git
      ```
2. Install requirements
     ```sh
     pip install -r requirements.txt
     ```
3. Go to your [Toggl Track](https://toggl.com/) profile and get the access token
4. Enter required settings to `settings.py`:
      * Start and end date of time frame you are interested in
      * Vacation days
      * Working hours per day
      * Toggl API token

      ```python
      #defines the time frame the script uses to calculate your over time
      start_date = datetime(2020, 1, 9)
      end_date = datetime.today()

      #to caluclate the target hours, the vacation_days in the chosen time frame are needed
      vacation_days = [
                       datetime(2020, 12, 30),
                       ]

      #working hours per day
      target_hours_per_day = 7

      #needed for authentification, you can find the token to your acc at the the end of the profile
      #settings page "https://track.toggl.com/profile"
      toggl_api = os.environ['TOGGL_API'] #my toggl api token is saved as environmental variable

      ```

## License
[MIT](https://choosealicense.com/licenses/mit/)
