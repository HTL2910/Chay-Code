import os
import pandas as pd

def combine_data():
    """Combine technical data with price/shipping data"""
    
    # Read the complete data from complete_final_extract
    complete_csv = os.path.join(os.path.dirname(__file__), "ooo", "complete_final_data.csv")
    
    try:
        # Read complete data
        df_complete = pd.read_csv(complete_csv)
        print(f"Loaded complete data: {len(df_complete)} records")
        print(f"Complete data columns: {df_complete.columns.tolist()}")
        
        # Use the complete data directly
        df_combined = df_complete.copy()
        
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
