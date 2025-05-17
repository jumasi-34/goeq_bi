from flask import Flask, request, render_template_string
import plotly.express as px

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def chart():
    selected = request.form.get("fruit", "Apple")  # 기본값: Apple

    # 샘플 데이터
    fruits = ["Apple", "Banana", "Cherry"]
    values = {"Apple": [3, 5, 7], "Banana": [6, 2, 4], "Cherry": [5, 8, 3]}

    fig = px.line(x=[1, 2, 3], y=values[selected], title=f"{selected} Trend")
    chart_html = fig.to_html(full_html=False)

    return render_template_string(
        """
    <html>
    <body>
      <form method="POST">
        <label for="fruit">Select fruit:</label>
        <select name="fruit" onchange="this.form.submit()">
          {% for item in fruits %}
            <option value="{{ item }}" {% if item == selected %}selected{% endif %}>{{ item }}</option>
          {% endfor %}
        </select>
      </form>
      <div>{{ chart|safe }}</div>
    </body>
    </html>
    """,
        chart=chart_html,
        fruits=fruits,
        selected=selected,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
