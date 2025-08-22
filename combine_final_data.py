import os
import pandas as pd

def combine_data():
    """Combine technical data with price/shipping data"""
    
    # Read the technical data from simple_extract
    technical_csv = os.path.join(os.path.dirname(__file__), "ooo", "simple_final_data.csv")
    price_csv = os.path.join(os.path.dirname(__file__), "ooo", "ultimate_final_data.csv")
    
    try:
        # Read technical data
        df_technical = pd.read_csv(technical_csv)
        print(f"Loaded technical data: {len(df_technical)} records")
        print(f"Technical columns: {df_technical.columns.tolist()}")
        
        # Read price data
        df_price = pd.read_csv(price_csv)
        print(f"Loaded price data: {len(df_price)} records")
        print(f"Price columns: {df_price.columns.tolist()}")
        
        # Check if price columns exist
        price_columns = ['price', 'days_to_ship', 'minimum_order_qty']
        available_price_columns = [col for col in price_columns if col in df_price.columns]
        print(f"Available price columns: {available_price_columns}")
        
        if available_price_columns:
            # Merge the data on part_number with suffixes
            merge_columns = ['part_number'] + available_price_columns
            df_combined = pd.merge(df_technical, df_price[merge_columns], 
                                  on='part_number', how='left', suffixes=('', '_price'))
            
            # Update price columns with price data
            for col in available_price_columns:
                price_col = f"{col}_price" if f"{col}_price" in df_combined.columns else col
                if price_col in df_combined.columns:
                    # Fill empty values in technical data with price data
                    mask = (df_combined[col] == '') | (df_combined[col].isna())
                    df_combined.loc[mask, col] = df_combined.loc[mask, price_col].fillna('')
                    
                    # Remove the duplicate column
                    if price_col != col:
                        df_combined = df_combined.drop(columns=[price_col])
        else:
            print("No price columns found, using technical data only")
            df_combined = df_technical.copy()
        
        print(f"Combined data: {len(df_combined)} records")
        
        # Show statistics
        print(f"\nFinal Results:")
        print(f"Total unique part numbers: {len(df_combined)}")
        print(f"Part numbers with price: {len(df_combined[df_combined['price'] != ''])}")
        print(f"Part numbers with days to ship: {len(df_combined[df_combined['days_to_ship'] != ''])}")
        print(f"Part numbers with minimum order qty: {len(df_combined[df_combined['minimum_order_qty'] != ''])}")
        print(f"Part numbers with inner diameter: {len(df_combined[df_combined['inner_dia_d'] != ''])}")
        print(f"Part numbers with outer diameter: {len(df_combined[df_combined['outer_dia_d'] != ''])}")
        print(f"Part numbers with width: {len(df_combined[df_combined['width_b'] != ''])}")
        print(f"Part numbers with load rating Cr: {len(df_combined[df_combined['basic_load_rating_cr'] != ''])}")
        print(f"Part numbers with load rating Cor: {len(df_combined[df_combined['basic_load_rating_cor'] != ''])}")
        print(f"Part numbers with weight: {len(df_combined[df_combined['weight'] != ''])}")
        
        # Save combined results
        output_csv = os.path.join(os.path.dirname(__file__), "ooo", "combined_final_data.csv")
        output_excel = os.path.join(os.path.dirname(__file__), "ooo", "combined_final_data.xlsx")
        
        df_combined.to_csv(output_csv, index=False)
        df_combined.to_excel(output_excel, index=False)
        
        print(f"\nResults saved to:")
        print(f"CSV: {output_csv}")
        print(f"Excel: {output_excel}")
        
        # Show sample data
        print("\nSample data:")
        print(df_combined.head(10).to_string())
        
        return df_combined
        
    except Exception as e:
        print(f"Error combining data: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    combine_data()
