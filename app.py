#!/usr/bin/env python
# coding: utf-8

# In[15]:


import pandas as pd
import os
from os  import getcwd
import pickle
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS


app = Flask(__name__)

CORS(app, origins="*")

directory = getcwd()


# # Import the required Pickle files

# In[6]:


prod_ranking_model = pd.read_pickle('prod_ranking_model.pkl')
cust_prod_ranking_model = pd.read_pickle('cust_prod_ranking_model.pkl')
cust_correlation_model = pd.read_pickle('cust_correlation_model.pkl')
prod_correlation_model = pd.read_pickle('prod_correlation_model.pkl')


# # HTML code for displaying Table

# In[7]:


# This function structures the HTML code for displaying the table on website
def html_code_table(prod_df,table_name,file_name,side):
    table_style = '<table style="border: 2px solid; float: ' + side + '; width: 40%;">'
    table_head = '<caption style="text-align: center; caption-side: top; font-size: 140%; font-weight: bold; color:black;"><strong>' + table_name + '</strong></caption>'
    table_head_row = '<tr><th>Product Name</th><th>Price (in Rs.)</th></tr>'
    
    html_code = table_style + table_head + table_head_row
    
    for i in range(len(prod_df.index)):
        row = '<tr><td>' + str(prod_df['Product'][i]) + '</td><td>' + str(prod_df['Rate'][i]) + '</td></tr>'
        html_code = html_code + row
        
    html_code = html_code + '</table>'
    
    file_path = os.path.join(directory,'templates/')
    
    hs = open(file_path + file_name + '.html', 'w')
    hs.write(html_code)
    
    #print(html_code)


# # Most Popular and Top Selling Products

# In[8]:


# This function calls the html_code_table function to create a .html file for Most Popular Products
def most_popular_table(get_response = False):
    most_popular_prods = prod_ranking_model.sort_values('Popularity_Rank',ascending=True)[['Product','Rate']].head(10).reset_index(drop=True)
    
    if get_response:
        return most_popular_prods
    else:
        html_code_table(most_popular_prods,'Most Popular Products','mostpopulartable','left')


# This function calls the html_code_table function to create a .html file for Top Selling Products
def top_sell_table(get_response = False):
    top_sell_prods = prod_ranking_model.sort_values('Top_Sell_Rank',ascending=True)[['Product','Rate']].head(10).reset_index(drop=True)
    
    if get_response:
        return top_sell_prods
    else:
        html_code_table(top_sell_prods,'Top Selling Products','topselltable','right')


# # Customer Frequently Purchased and Purchased the Most Products

# In[9]:


# This function calls the html_code_table function to create a .html file for Most Popular Products of a Customer
def cust_most_popular_table(cust_name , get_response = False):
    cust_most_popular_prods = cust_prod_ranking_model[cust_prod_ranking_model['Party'] == cust_name]
    cust_most_popular_prods = cust_most_popular_prods.sort_values('Popularity_Rank',ascending=True)[['Product','Rate']].head(10).reset_index(drop=True)
    
    if get_response:
        return cust_most_popular_prods
    else:
        html_code_table(cust_most_popular_prods,'Products you Frequently Purchased','custmostpopulartable','left')
    

# This function calls the html_code_table function to create a .html file for Top Selling Products of a Customer
def cust_top_sell_table(cust_name , get_response = False):
    cust_top_sell_prods = cust_prod_ranking_model[cust_prod_ranking_model['Party'] == cust_name]
    cust_top_sell_prods = cust_top_sell_prods.sort_values('Top_Sell_Rank',ascending=True)[['Product','Rate']].head(10).reset_index(drop=True)
    
    if get_response:
        return cust_top_sell_prods
    else:
        html_code_table(cust_top_sell_prods,'Products you Purchased the Most','custtopselltable','right')
    


# # Products Customer may Like

# In[10]:


# This function performs the below functionality for the input customer
# - get the list of customers with similar purchasing pattern and correlation coefficient
# - for each customer from the list,
#   - get the products purchased
#   - multiply the purchased qty with customer correlation coefficient
# - aggregate the qty_corr by product
# - ignore the products already purchased by the input customer
# - sort them by the qty_corr
# - calls the html_code_table function to create a .html file for top 10 products customer may like

def recommend_prod_cust_table(cust_name , get_response = False):
    similar_custs_corr = cust_correlation_model.loc[cust_name].sort_values(ascending=False)
    
    prod_by_similar_custs = pd.DataFrame()
    
    # get the products purchased by each customer and multiply with the customer correlation coefficient
    for i in range(len(similar_custs_corr)):
        if similar_custs_corr.index[i] != cust_name:
            cust_top_sell_prods = cust_prod_ranking_model[cust_prod_ranking_model['Party'] == similar_custs_corr.index[i]]
            cust_top_sell_prods = cust_top_sell_prods[['Product','Qty','Rate']].reset_index(drop=True)
            cust_top_sell_prods['Qty_Corr'] = cust_top_sell_prods['Qty'] * similar_custs_corr.iloc[i]
            prod_by_similar_custs = pd.concat([cust_top_sell_prods,prod_by_similar_custs])
    
    # aggregate the Qty Correlation by Product
    prod_by_similar_custs = prod_by_similar_custs.groupby('Product').agg({'Qty_Corr':'sum','Rate':'max'})
    prod_by_similar_custs.reset_index(inplace=True)
    #print(prod_by_similar_custs.head(20))
    
    # ignore the products already purchased by the input customer
    # merge prod_by_similar_custs and customer purchased products and drop the rows with No_of_orders being Not Null
    input_cust_top_sell_prods = cust_prod_ranking_model[cust_prod_ranking_model['Party'] == cust_name]
    df_merge = pd.merge(prod_by_similar_custs,input_cust_top_sell_prods[['Product','No_of_Orders']],how='left',on='Product')
    prod_recommend_to_cust = df_merge[df_merge['No_of_Orders'].isnull()]
    
    # sort the dataframe on Qty_Corr
    prod_recommend_to_cust = prod_recommend_to_cust.sort_values('Qty_Corr',ascending=False)[['Product','Rate']].head(10).reset_index(drop=True)
    
    #print(prod_recommend_to_cust)
    
    if get_response:
        return prod_recommend_to_cust
    else:
        html_code_table(prod_recommend_to_cust,'Products you may like','prodrecommendtable','center')
    


# # Similar Products to Display

# In[19]:


# This function performs the below functionality for the input product
# - get the list of products with similar purchasing pattern and correlation coefficient
# - get the price of each product from prod_ranking_model
# - get the price of input product and return to main
# - drop the product in view from the list
# - sort them by the correlation coefficient
# - calls the html_code_table function to create a .html file for top 10 products similar to the product in view

def similar_prods_table(prod_name , get_response = False):
    similar_prods_corr = prod_correlation_model.loc[prod_name].sort_values(ascending=False)
    
    similar_prods = pd.merge(similar_prods_corr,prod_ranking_model[['Product','Rate']],how='left',on='Product')
    
    prod_price = similar_prods[similar_prods['Product'] == prod_name]['Rate'].values[0]
    
    input_prod_index = similar_prods[similar_prods['Product'] == prod_name].index
    similar_prods.drop(index=input_prod_index,inplace=True)
    
    similar_prods = similar_prods[['Product','Rate']].head(10).reset_index(drop=True)
    
    #print(similar_prods)
    
    
    if get_response:
        return similar_prods
    else:
        html_code_table(similar_prods,'Customers who purchased this product also purchased these','similarprodtable','left')
        return prod_price
 

# In[12]:


@app.route("/")
def home():
    most_popular_table()
    top_sell_table()
        
    return render_template('home.html')

@app.route("/custhome")
def custhome():
    most_popular_table()
    top_sell_table()
    print(cust_prod_ranking_model['Party'].unique()[0])

    cust_name = float(request.args.get('name'))

    if cust_name in cust_prod_ranking_model['Party'].unique():
        cust_most_popular_table(cust_name)
        cust_top_sell_table(cust_name)
        recommend_prod_cust_table(cust_name)
        return render_template('cust_home.html',name=str(cust_name),new='n')
    else:
        return render_template('cust_home.html',name=str(cust_name),new='y')
 
@app.route("/productview")
def productview():

    prod_name = str(request.args.get('prod')).upper()
    
    if prod_name in prod_ranking_model['Product'].unique():
        prod_price = similar_prods_table(prod_name)
        print(prod_price)
        print(prod_name)
        return render_template('prod_view.html',prod=prod_name,price=prod_price,exists='y')
    else:
        return render_template('prod_view.html',prod=prod_name,exists='n')

@app.route("/mostpopular")
def mostpopular():
    
    most_popular_prods = most_popular_table(get_response = True)
    response = {
        'products': most_popular_prods.to_dict(orient='records'),
    }
    return jsonify(response), 200

@app.route("/topselling")
def topselling():
   
    top_sell_prods = top_sell_table(get_response=True)
    response = {
        'products': top_sell_prods.to_dict(orient='records')
    }
    return jsonify(response), 200

@app.route("/similarproducts")
def similarproducts():
    
    # Get the product name from the request parameters
    prod_name = request.args.get('prod')

    # Check if the product name is provided
    if not prod_name:
        return jsonify({'error': 'Product name is required'}), 400

    # Convert the product name to uppercase
    prod_name = prod_name.upper()

    # Check if the product exists in the data
    if prod_name not in prod_ranking_model['Product'].unique():
        return jsonify({'error': 'Product not found'}), 404

    # Perform calculations or any other processing here
    similar_prods = similar_prods_table(prod_name , get_response = True)
    
    # Create a response object
    response = {
        'product': prod_name,
        'products': similar_prods.to_dict(orient='records')
    }

    # Return the response as JSON
    return jsonify(response), 200

@app.route("/cust_freq_purchased")
def cust_freq_purchased():
    
    cust_name = request.args.get('name')
    
    if not cust_name:
        return jsonify({'error': 'Customer id is required'}), 400
    
    try:
        cust_name = float(cust_name)
    except:
        return jsonify({'error': 'Customer id is required'}), 400
    
    if cust_name not in cust_prod_ranking_model['Party'].unique():
        return jsonify({'error': 'Customer not found'}), 404
    
    cust_most_popular_prods = cust_most_popular_table(cust_name , get_response = True)
    
    response = {
        'customer': cust_name,
        'products': cust_most_popular_prods.to_dict(orient='records')
    }

    return jsonify(response), 200
    
@app.route("/cust_most_purchased")
def cust_most_purchased():
    
    cust_name = request.args.get('name')
    
    if not cust_name:
        return jsonify({'error': 'Customer id is required'}), 400
    
    try:
        cust_name = float(cust_name)
    except:
        return jsonify({'error': 'Customer id is required'}), 400
    
    if cust_name not in cust_prod_ranking_model['Party'].unique():
        return jsonify({'error': 'Customer not found'}), 404
    
    cust_top_sell_prods = cust_top_sell_table(cust_name , get_response = True)
    
    response = {
        'customer': cust_name,
        'products': cust_top_sell_prods.to_dict(orient='records')
    }

    return jsonify(response), 200

@app.route("/recommend_prod_cust")
def recommend_prod_cust():
   
    cust_name = request.args.get('name')
    
    if not cust_name:
        return jsonify({'error': 'Customer id is required'}), 400
    
    try:
        cust_name = float(cust_name)
    except:
        return jsonify({'error': 'Customer id is required'}), 400
    
    if cust_name not in cust_prod_ranking_model['Party'].unique():
        return jsonify({'error': 'Customer not found'}), 404
    
    prod_recommend_to_cust = recommend_prod_cust_table(cust_name , get_response=True)
    
    response = {
        'customer': cust_name,
        'products': prod_recommend_to_cust.to_dict(orient='records')
    }

    return jsonify(response), 200


if __name__ == "__main__":
    app.run(debug=True)
