import streamlit as st
import pandas as pd
import plotly.express as px


# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Data Insights", layout="wide")
st.title("📊 Data Insights – Smart Visualization Dashboard")

# ---------------- HELPERS ----------------
def make_columns_unique(columns):
    seen = {}
    new_cols = []
    for col in columns:
        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}.{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)
    return new_cols

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader(
    "Upload Excel / CSV File",
    type=["xlsx", "xls", "csv"]
)

if uploaded_file:

    # ---------- READ FILE ----------
    name = uploaded_file.name
    if name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    elif name.endswith(".xls"):
        df = pd.read_excel(uploaded_file, engine="xlrd")
    else:
        df = pd.read_csv(uploaded_file)

    df.columns = make_columns_unique(df.columns)

    st.success("✅ File uploaded successfully")

    # ---------------- DATASET SUMMARY ----------------
    st.subheader("📌 Dataset Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", df.shape[0])
    c2.metric("Columns", df.shape[1])
    c3.metric("Missing Values", int(df.isna().sum().sum()))
    c4.metric("Duplicate Rows", int(df.duplicated().sum()))

    # ---------------- PREVIEW ----------------
    st.subheader("📄 Data Preview")
    st.dataframe(df.head(200), use_container_width=True)

    # ---------------- COLUMN TYPES ----------------
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

    st.subheader("🧠 Column Types")
    st.markdown(
        f"""
        **Categorical Columns:**  
        {", ".join(categorical_cols) if categorical_cols else "None"}

        **Numeric Columns:**  
        {", ".join(numeric_cols) if numeric_cols else "None"}
        """
    )

    # ---------------- MULTI-CHART STATE ----------------
    if "chart_configs" not in st.session_state:
        st.session_state.chart_configs = []

    # ---------------- ADD CHART ----------------
    st.subheader("📊 Chart Configuration")

    if st.button("➕ Add Chart"):
        st.session_state.chart_configs.append({
            "chart_type": "Bar",
            "x": df.columns[0],
            "y": None,
            "use_agg": False,
            "agg": None,
            "top_n": 15,
            "color_scheme": "Plotly"
        })

    # ---------------- CHART CONFIG CARDS ----------------
    for i, cfg in enumerate(st.session_state.chart_configs):
        with st.container():
            st.markdown(f"### Chart {i + 1}")

            c1, c2, c3, c4, c5 = st.columns(5)

            cfg["chart_type"] = c1.selectbox(
                "Chart Type",
                ["Bar", "Line", "Pie", "Doughnut"],
                key=f"type_{i}"
            )

            cfg["x"] = c2.selectbox(
                "Category Column",
                df.columns,
                key=f"x_{i}"
            )

            cfg["use_agg"] = c3.checkbox(
                "Use Aggregation",
                key=f"agg_check_{i}"
            )

            if cfg["chart_type"] in ["Bar", "Line"] and cfg["use_agg"]:
                cfg["y"] = c4.selectbox(
                    "Value Column",
                    numeric_cols,
                    key=f"y_{i}"
                )
                cfg["agg"] = st.selectbox(
                    "Aggregation",
                    ["Sum", "Mean", "Count"],
                    key=f"agg_{i}"
                )
            else:
                cfg["y"] = None
                cfg["agg"] = None

            cfg["color_scheme"] = c5.selectbox(
                "Color Theme",
                ["Plotly", "Set1", "Set2", "Set3", "Dark2", "Pastel"],
                key=f"color_{i}"
            )

            cfg["top_n"] = st.slider(
                "Top N (reduce clutter)",
                5, 30, cfg["top_n"],
                key=f"top_{i}"
            )

            st.divider()

    # ---------------- GENERATE ALL CHARTS ----------------
    if st.button("📈 Generate All Charts"):
        st.subheader("📊 Generated Charts")

        for i, cfg in enumerate(st.session_state.chart_configs):

            x = cfg["x"]
          
            colors = getattr(px.colors.qualitative, cfg["color_scheme"])

            # -------- BAR / LINE --------
            if cfg["chart_type"] in ["Bar", "Line"]:

                if cfg["use_agg"] and cfg["y"]:
                    if cfg["agg"] == "Sum":
                        plot_df = df.groupby(x)[cfg["y"]].sum().reset_index(name="value")
                    elif cfg["agg"] == "Mean":
                        plot_df = df.groupby(x)[cfg["y"]].mean().reset_index(name="value")
                    else:
                        plot_df = df.groupby(x)[cfg["y"]].count().reset_index(name="value")
                else:
                    plot_df = df[x].value_counts().reset_index(name="value")
                    plot_df.columns = [x, "value"]

                

                fig = px.bar(
                    plot_df,
                    x=x,
                    y="value",
                    color=x,
                    color_discrete_sequence=colors,
                    title=f"Chart {i + 1}"
                ) if cfg["chart_type"] == "Bar" else px.line(
                    plot_df,
                    x=x,
                    y="value",
                    markers=True,
                    color_discrete_sequence=colors,
                    title=f"Chart {i + 1}"
                )

            # -------- PIE / DOUGHNUT --------
            else:
                plot_df = df[x].value_counts().reset_index()
                plot_df.columns = [x, "value"]
                

                fig = px.pie(
                    plot_df,
                    names=x,
                    values="value",
                    hole=0.45 if cfg["chart_type"] == "Doughnut" else 0,
                    color=x,
                    color_discrete_sequence=colors,
                    title=f"Chart {i + 1}"
                )

            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

    # ---------------- FINAL SUMMARY ----------------
    st.subheader("📈 Dataset Summary")

    if numeric_cols:
        st.markdown("**Numeric Statistics**")
        st.dataframe(df[numeric_cols].describe().round(2))

    st.subheader("📊 Category Frequencies (Top Values)")

    freq_rows = []

    for col in categorical_cols:
        vc = df[col].value_counts().head(5)
        for category, count in vc.items():
            freq_rows.append({
                "Column": col,
                "Category": str(category),
                "Count": int(count)
            })

    freq_table = pd.DataFrame(freq_rows)

# Optional: sort by column name then count
    freq_table = freq_table.sort_values(
        by=["Column", "Count"],
        ascending=[True, False]
    )

# Display as compact table
    st.dataframe(
        freq_table,
        use_container_width=False,
        hide_index=True,
        height=350
    )



    # ---------------- QUERY SECTION ----------------
    st.subheader("🤖 Queries (AI-ready)")

    query = st.text_input(
        "Ask something like: Which car brand has the highest average price?"
    )

    if query:
        q = query.lower()

        if "highest" in q and "price" in q and "make" in df.columns:
            ans = df.groupby("make")["price"].mean().sort_values(ascending=False).head(1)
            st.success(f"🏆 Best brand by average price: **{ans.index[0]}**")

        elif "most" in q and "cars" in q and "make" in df.columns:
            ans = df["make"].value_counts().head(1)
            st.success(f"🚗 Brand with most cars: **{ans.index[0]}**")

        else:
            st.info("This query needs AI-based understanding (can be added later).")

else:
    st.info("👆 Upload a dataset to begin")


