import matplotlib.pyplot as plot

data_sources = {
    'Classic Schema': 9999 + 9967,
    'AVM Modules': 506
}

labels = list(data_sources.keys())
sizes = list(data_sources.values())
colors = ['#1E3A8A', "#C02000"]

plot.figure(figsize=(10, 10))
plot.pie(
    sizes, 
    labels=labels, 
    colors=colors,
    autopct=lambda p: '{:.1f}%\n({:,.0f} docs)'.format(p, p * sum(sizes) / 100), # Show percentage and raw count
    startangle=140,
    pctdistance=0.75,
    textprops={'color': 'white', 'fontsize': 18, 'fontweight': 'bold'},
    labeldistance=1.1
)

plot.title('RAG Data Source Composition in Azure AI Search Index', fontsize=20, fontweight='bold', pad=20)
plot.legend(labels, loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=2, fontsize=18, frameon=True)

# Ensure the pie chart is circular
plot.axis('equal') 

plot.savefig('rag_data_composition.png')
print("Chart 'rag_data_composition.png' saved successfully.")