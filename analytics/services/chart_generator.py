def format_analytics_data(columns, rows, chart_type='bar', chart_title="Database Analytics"):
    """
    Transforms tabular database query results into formatted chart configuration (labels, series/datasets)
    and generates automated AI data insights & trend detection.
    """
    if not columns or not rows:
        return {
            "title": chart_title,
            "chart_type": chart_type,
            "labels": ["No Data"],
            "series": [0],
            "insights": "No data available to plot."
        }

    # Identify label column (usually textual/categorical) and metric column (numeric)
    label_col_idx = 0
    metric_col_idx = 1 if len(columns) > 1 else 0

    for idx, col in enumerate(columns):
        # Check first non-null sample row
        val = rows[0][idx] if rows else None
        if isinstance(val, (int, float)) and metric_col_idx == 1:
            metric_col_idx = idx
            break

    labels = []
    series_data = []

    for r in rows[:20]:  # Cap chart points for readability
        lbl = str(r[label_col_idx]) if r[label_col_idx] is not None else "N/A"
        try:
            val = float(r[metric_col_idx]) if r[metric_col_idx] is not None else 0.0
        except (ValueError, TypeError):
            val = 0.0

        labels.append(lbl)
        series_data.append(val)

    # Automated Trend Detection & Insights
    insights = []
    if series_data:
        max_val = max(series_data)
        min_val = min(series_data)
        avg_val = round(sum(series_data) / len(series_data), 2)
        max_label = labels[series_data.index(max_val)]
        min_label = labels[series_data.index(min_val)]

        insights.append(f"Highest value recorded is **{max_val:,.2f}** under category **'{max_label}'**.")
        insights.append(f"Lowest recorded metric is **{min_val:,.2f}** under **'{min_label}'**.")
        insights.append(f"Average distribution across top groups is **{avg_val:,.2f}**.")

        # Trend direction
        if len(series_data) > 1:
            if series_data[-1] > series_data[0]:
                insights.append("Trend Analysis: An overall upward growth trend is detected across records.")
            elif series_data[-1] < series_data[0]:
                insights.append("Trend Analysis: A downward contraction trajectory is observed.")
            else:
                insights.append("Trend Analysis: Values remain stable with steady distribution.")

    return {
        "title": chart_title,
        "chart_type": chart_type,
        "x_axis_name": columns[label_col_idx] if label_col_idx < len(columns) else "Category",
        "y_axis_name": columns[metric_col_idx] if metric_col_idx < len(columns) else "Value",
        "labels": labels,
        "series": series_data,
        "insights": " ".join(insights)
    }
