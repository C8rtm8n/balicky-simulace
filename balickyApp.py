import pandas as pd
from sklearn.cluster import KMeans
import streamlit as st
from io import BytesIO

# Load data from the uploaded Excel file
@st.cache_data
def load_data():
    file_path = "DATA_test.xlsx"  # Replace with the path to your file if running locally
    return pd.read_excel(file_path, sheet_name="komponenty")

data = load_data()

# Title
st.title("Simulace rozdělení konstrukcí do balíčků")

# Display input data
if st.checkbox("Zobrazit vstupní data"):
    st.dataframe(data)

# Checkbox list for selecting components
components = data["KOMPONENTA"].unique()
selected_components = st.multiselect(
    "Vyberte komponenty pro zahrnutí do simulace:", options=components, default=components
)

# Filter data based on selected components
filtered_data = data[data["KOMPONENTA"].isin(selected_components)]

# Input for number of packages
num_packages = st.slider("Počet balíčků:", min_value=2, max_value=10, value=3, step=1)

# Perform KMeans clustering
if st.button("Spustit simulaci"):
    # Group by construction and sum the relevant quantities and weights for clustering
    grouped_data = filtered_data.groupby("KONSTRUKCE").agg({"MNOZSTVI": "sum", "HMOTNOST": "sum"}).reset_index()

    # KMeans clustering
    kmeans = KMeans(n_clusters=num_packages, random_state=42)
    grouped_data["Balíček"] = kmeans.fit_predict(grouped_data[["MNOZSTVI"]])

    # Display results
    st.subheader("Výsledky rozdělení do balíčků")
    all_packages = []
    for i in range(num_packages):
        package = grouped_data[grouped_data["Balíček"] == i]
        st.write(f"### Balíček {chr(65 + i)}")
        st.dataframe(package)

        # Calculate total weight of the package
        total_weight = package["HMOTNOST"].sum()
        st.write(f"Celková hmotnost balíčku: {total_weight:.2f} kg")

        # List components and their quantities in the package
        components_in_package = filtered_data[filtered_data["KONSTRUKCE"].isin(package["KONSTRUKCE"])]
        st.write("#### Komponenty v balíčku:")
        package_details = components_in_package[["KOMPONENTA", "MNOZSTVI"]].groupby("KOMPONENTA").sum().reset_index()
        st.dataframe(package_details)

        # Store package details for export
        package["Komponenty"] = package_details.apply(lambda row: f"{row['KOMPONENTA']}: {row['MNOZSTVI']}", axis=1).str.cat(sep="; ")
        all_packages.append(package)

    # Optionally show total quantities and weights per package
    st.subheader("Shrnutí balíčků")
    summary = grouped_data.groupby("Balíček").agg({"MNOZSTVI": "sum", "HMOTNOST": "sum"}).reset_index()
    st.dataframe(summary)

    # Export results to Excel for download
    export_file = BytesIO()
    pd.concat(all_packages).to_excel(export_file, index=False, engine='openpyxl')
    export_file.seek(0)

    st.download_button(
        label="Stáhnout výsledky jako Excel",
        data=export_file,
        file_name="balicky_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Note for sharing the app
st.info("Aplikaci můžete nasdílet pomocí Streamlit Community Cloud nebo jiného hostingu.")
