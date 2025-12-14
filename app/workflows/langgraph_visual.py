import streamlit as st

def graph_dot():
    """Visualisierung des Prozesses mit Graphviz."""
    dot = r"""
    digraph G {
        rankdir=LR;
        node [
            shape=box,
            style="rounded,filled",
            color="#9ca3af",
            fillcolor="#f9fafb",
            fontname="Inter"
        ];

        input      [label="Input (Text)"];
        reader     [label="Reader (strukturieren)"];
        summarizer [label="Summarizer"];
        critic     [label="Critic"];
        integrator [label="Integrator"];
        output     [label="Output (Structured, Summary, Critic, Meta)"];

        input -> reader -> summarizer -> critic -> integrator -> output;
    }
    """.strip()
    st.graphviz_chart(dot, use_container_width=True)
