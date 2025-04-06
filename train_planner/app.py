import streamlit as st
import pandas as pd
import uuid
import base64
import plotly.express as px

from modules.data_manager import DataManager
from modules.visualizer import Visualizer
from modules.analyzer import Analyzer
from utils.import_export import export_schedule_to_json, import_schedule_from_json, export_schedule_to_csv
from utils.time_utils import parse_time, minutes_to_hhmm
from models.station import Station
from models.train import Train
from models.schedule import Schedule

# Page config
st.set_page_config(
    page_title="Railway Timetable Visualization Tool",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        padding-top: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px;
        padding: 10px 16px;
        font-size: 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e6f0ff;
        border-bottom: 2px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
DataManager.initialize_session_state()
Visualizer.initialize_session_state()

def main():
    """Main application entry point."""
    # Page title
    st.title("Railway Timetable Visualization Tool")
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Go to",
            ["Station Management", "Train Scheduling", "Visualization", "Analysis", "Import/Export"]
        )
        
        st.markdown("---")
        
        # Show current data summary
        st.subheader("Current Data")
        st.write(f"Stations: {len(st.session_state.stations)}")
        st.write(f"Trains: {len(st.session_state.trains)}")
        
        st.markdown("---")
        
        # Instructions
        with st.expander("Instructions", expanded=False):
            st.markdown("""
            ### Quick Start Guide
            
            1. First, add stations in the **Station Management** page
            2. Create train schedules in the **Train Scheduling** page
            3. View the time-space diagram in the **Visualization** page
            4. Analyze your schedule in the **Analysis** page
            5. Save or load your work in the **Import/Export** page
            
            ### Tips
            
            - Use templates to quickly create common train patterns
            - You can edit existing trains by selecting them in the "View Trains" tab
            - Adjust the time range in the visualization to focus on specific periods
            - Check for conflicts in the Analysis page before finalizing your schedule
            """)
    
    # Main content
    if page == "Station Management":
        DataManager.manage_stations_ui()
    
    elif page == "Train Scheduling":
        DataManager.manage_trains_ui()
    
    elif page == "Visualization":
        Visualizer.visualize_schedule_ui()
    
    elif page == "Analysis":
        Analyzer.analyze_schedule_ui()
    
    elif page == "Import/Export":
        display_import_export_ui()

def display_import_export_ui():
    """Display import/export interface."""
    st.header("Import & Export")
    
    tabs = st.tabs(["Export Schedule", "Import Schedule"])
    
    # Export tab
    with tabs[0]:
        st.subheader("Export Current Schedule")
        
        if not st.session_state.stations or not st.session_state.trains:
            st.warning("No data to export. Please add stations and trains first.")
        else:
            # Create a Schedule object from session state
            schedule = create_schedule_from_session()
            
            # Export as JSON
            json_data = export_schedule_to_json(schedule)
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name="railway_schedule.json",
                mime="application/json"
            )
            
            # Export as CSV
            csv_data = export_schedule_to_csv(schedule)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="railway_schedule.csv",
                mime="text/csv"
            )
            
            # Display preview
            with st.expander("Preview JSON Data", expanded=False):
                st.code(json_data, language="json")
            
            with st.expander("Preview CSV Data", expanded=False):
                st.code(csv_data)
    
    # Import tab
    with tabs[1]:
        st.subheader("Import Schedule")
        
        uploaded_file = st.file_uploader("Upload JSON Schedule", type=["json"])
        
        if uploaded_file is not None:
            # Read and parse the file
            json_data = uploaded_file.read().decode("utf-8")
            
            # Try to import
            imported_schedule = import_schedule_from_json(json_data)
            
            if imported_schedule:
                st.success("Schedule imported successfully!")
                
                # Preview the imported data
                with st.expander("Preview Imported Data", expanded=True):
                    st.write(f"Schedule Name: {imported_schedule.name}")
                    st.write(f"Stations: {len(imported_schedule.stations)}")
                    st.write(f"Trains: {len(imported_schedule.trains)}")
                    
                    # Show stations
                    st.write("**Stations:**")
                    st.write(", ".join([s.name for s in imported_schedule.stations]))
                    
                    # Show trains
                    st.write("**Trains:**")
                    for train in imported_schedule.trains:
                        st.write(f"- {train.name} ({len(train.schedule)} stops)")
                
                # Confirm import button
                if st.button("Confirm Import (Replace Current Data)"):
                    load_schedule_to_session(imported_schedule)
                    st.success("Data loaded into the application!")
                    st.experimental_rerun()
            else:
                st.error("Failed to import schedule. The file may be invalid.")

def create_schedule_from_session():
    """
    Create a Schedule object from session state data.
    
    Returns:
        Schedule: Schedule object with current data.
    """
    stations = st.session_state.stations
    
    # Convert train dictionaries to Train objects
    trains = []
    for train_dict in st.session_state.trains:
        train = Train(
            name=train_dict['name'],
            color=train_dict['color'],
            schedule=train_dict['schedule']
        )
        trains.append(train)
    
    return Schedule(
        name="Railway Schedule",
        stations=stations,
        trains=trains
    )

def load_schedule_to_session(schedule):
    """
    Load a Schedule object into session state.
    
    Args:
        schedule (Schedule): Schedule object to load.
    """
    # Set stations
    st.session_state.stations = schedule.stations
    
    # Convert Train objects to dictionaries
    trains = []
    for train in schedule.trains:
        train_dict = {
            'name': train.name,
            'color': train.color,
            'schedule': train.schedule
        }
        trains.append(train_dict)
    
    st.session_state.trains = trains
    
    # Reset selected train
    st.session_state.selected_train_idx = None
    
    # Update form key
    st.session_state.train_form_key = str(uuid.uuid4())

if __name__ == "__main__":
    main()