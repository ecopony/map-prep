import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import box
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
import sys
import warnings
from tqdm import tqdm

# Check for required dependencies
def check_dependencies() -> None:
    """Check if all required dependencies are available."""
    required_packages = ['geopandas', 'matplotlib', 'numpy', 'shapely', 'tqdm']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        raise ImportError(f"Missing required packages: {', '.join(missing)}")

# Call dependency check on import
check_dependencies()


class TopoBlockDesigner:
    """Creates artistic topographic block designs from contour shapefiles."""
    
    def __init__(self, contour_shapefile: Union[str, Path], border_shapefile: Optional[Union[str, Path]] = None):
        """
        Initialize with paths to your contour and border shapefiles.
        
        Args:
            contour_shapefile: Path to contour shapefile (.shp)
            border_shapefile: Optional path to border shapefile (.shp)
            
        Raises:
            FileNotFoundError: If shapefile doesn't exist
            ValueError: If shapefile is empty or invalid
        """
        # Validate and load contour shapefile
        contour_path = Path(contour_shapefile)
        if not contour_path.exists():
            raise FileNotFoundError(f"Contour shapefile not found: {contour_path}")
        
        try:
            self.contours = gpd.read_file(contour_path)
        except Exception as e:
            raise ValueError(f"Failed to read contour shapefile: {e}")
            
        if self.contours.empty:
            raise ValueError("Contour shapefile is empty")
        
        # Validate and load border shapefile if provided
        self.border = None
        if border_shapefile:
            border_path = Path(border_shapefile)
            if not border_path.exists():
                warnings.warn(f"Border shapefile not found: {border_path}, ignoring...")
            else:
                try:
                    self.border = gpd.read_file(border_path)
                    if self.border.empty:
                        warnings.warn("Border shapefile is empty, ignoring...")
                        self.border = None
                except Exception as e:
                    warnings.warn(f"Failed to read border shapefile: {e}, ignoring...")
        
        # Ensure CRS compatibility
        if self.border is not None and self.contours.crs != self.border.crs:
            warnings.warn("Contours and border have different CRS, reprojecting border...")
            self.border = self.border.to_crs(self.contours.crs)

        # Get bounds from border if available, otherwise from contours
        if self.border is not None:
            self.bounds = self.border.total_bounds
        else:
            self.bounds = self.contours.total_bounds

        self.minx, self.miny, self.maxx, self.maxy = self.bounds
        self.width = self.maxx - self.minx
        self.height = self.maxy - self.miny
        
        # Validate bounds
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Invalid bounds: width={self.width}, height={self.height}")
    
    def _optimize_contour_clipping(self, block_geometries: List) -> List[gpd.GeoDataFrame]:
        """
        Optimized contour clipping using spatial indexing and batch operations.
        
        Args:
            block_geometries: List of block geometries for clipping
            
        Returns:
            List of clipped contour GeoDataFrames for each block
        """
        clipped_results = []
        
        # Create spatial index for faster intersections
        contour_sindex = self.contours.sindex
        
        for block_geom in block_geometries:
            # Use spatial index to find potential intersections
            possible_matches_index = list(contour_sindex.intersection(block_geom.bounds))
            possible_matches = self.contours.iloc[possible_matches_index]
            
            if not possible_matches.empty:
                # Clip only the potential matches
                clipped = possible_matches.clip(block_geom)
                clipped_results.append(clipped[~clipped.is_empty])
            else:
                clipped_results.append(gpd.GeoDataFrame())
        
        return clipped_results

    def create_block_design(self, mountain_name: str, output_path: Union[str, Path], 
                          colors: List[str] = None,
                          gap_percent: float = 0.005, 
                          dpi: int = 300,
                          figsize: Tuple[float, float] = (12, 12),
                          line_width: float = 0.8,
                          background_color: str = 'transparent',
                          text_size: Optional[int] = None,
                          adaptive_text: bool = True,
                          show_text: bool = True) -> None:
        """
        Create the three-block design with topo cutouts.
        
        Args:
            mountain_name: Text to display (e.g., "Mt Adams")
            output_path: Where to save the PNG
            colors: List of 3 colors for the blocks (defaults to red-teal-blue)
            gap_percent: Percentage of width for gaps between blocks
            dpi: Output resolution
            figsize: Figure size in inches
            line_width: Width of contour lines
            background_color: Background color
            text_size: Font size for mountain name (auto-calculated if None)
            adaptive_text: Whether to adapt text size to figure dimensions
            show_text: Whether to display the mountain name text
            
        Raises:
            ValueError: If invalid parameters provided
            IOError: If output path cannot be written
        """
        # Set default colors - t-shirt friendly monochrome
        if colors is None:
            colors = ['#1A1A1A', '#333333', '#4D4D4D']
            
        # Validate inputs
        if len(colors) != 3:
            raise ValueError("Exactly 3 colors must be provided")
        if not (0 <= gap_percent <= 0.5):
            raise ValueError("gap_percent must be between 0 and 0.5")
        if dpi <= 0:
            raise ValueError("dpi must be positive")
            
        # Ensure output directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate block dimensions
        gap_size = self.width * gap_percent
        block_width = (self.width - (2 * gap_size)) / 3
        
        # Create figure with background
        fig, ax = plt.subplots(1, 1, figsize=figsize)
        if background_color != 'transparent':
            fig.patch.set_facecolor(background_color)
            ax.set_facecolor(background_color)
        else:
            fig.patch.set_facecolor('none')
            ax.set_facecolor('none')
        
        # Set the plot limits
        ax.set_xlim(self.minx, self.maxx)
        ax.set_ylim(self.miny, self.maxy)
        ax.set_aspect('equal')
        
        # Create three rectangles with contour cutouts - SIMPLE VERSION
        for i, color in enumerate(colors):
            # Calculate block position
            left = self.minx + i * (block_width + gap_size)
            right = left + block_width

            # Create rectangle
            block_geom = box(left, self.miny, right, self.maxy)

            # Find contours in this rectangle
            contour_sindex = self.contours.sindex
            possible_matches_index = list(contour_sindex.intersection(block_geom.bounds))

            if possible_matches_index:
                # Get contours that intersect this block
                possible_matches = self.contours.iloc[possible_matches_index]
                clipped_contours = possible_matches.clip(block_geom)
                clipped_contours = clipped_contours[~clipped_contours.is_empty]

                if not clipped_contours.empty:
                    # Buffer the contour lines to create cutout width
                    buffer_distance = line_width * (self.width / 500)

                    # Suppress the geographic CRS warning - we accept the approximation
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", message=".*geographic CRS.*")
                        buffered_contours = clipped_contours.geometry.buffer(buffer_distance)

                    # Union all buffered contours and subtract from block
                    from shapely.ops import unary_union
                    if len(buffered_contours) > 0:
                        contour_union = unary_union(buffered_contours.values)
                        block_with_cutouts = block_geom.difference(contour_union)

                        # Plot the result
                        if not block_with_cutouts.is_empty:
                            cutout_gdf = gpd.GeoDataFrame([1], geometry=[block_with_cutouts], crs=self.contours.crs)
                            cutout_gdf.plot(ax=ax, color=color, zorder=1)
                        else:
                            # Entire block was cut out - just skip it or draw outline
                            pass
                    else:
                        # No buffers, draw solid block
                        block_gdf = gpd.GeoDataFrame([1], geometry=[block_geom], crs=self.contours.crs)
                        block_gdf.plot(ax=ax, color=color, zorder=1)
                else:
                    # No contours, draw solid block
                    block_gdf = gpd.GeoDataFrame([1], geometry=[block_geom], crs=self.contours.crs)
                    block_gdf.plot(ax=ax, color=color, zorder=1)
            else:
                # No contours, draw solid block
                block_gdf = gpd.GeoDataFrame([1], geometry=[block_geom], crs=self.contours.crs)
                block_gdf.plot(ax=ax, color=color, zorder=1)
        
        
        # Add mountain name text below rectangles, aligned right
        if mountain_name and show_text:
            # Calculate text position - very close to the bottom of rectangles, aligned right
            text_y = self.miny - (self.height * 0.02)  # Very close to rectangles
            text_x = self.maxx  # Right edge for right alignment

            # Calculate adaptive text size if not specified
            if text_size is None and adaptive_text:
                # Base text size on figure width, with reasonable bounds
                base_size = min(figsize) * 3  # Scale with figure size
                calculated_size = max(12, min(48, base_size))
            else:
                calculated_size = text_size or 24

            # Add text with serif font
            ax.text(text_x, text_y, mountain_name,
                   fontsize=calculated_size,
                   color='white',
                   weight='normal',
                   horizontalalignment='right',
                   verticalalignment='top',
                   family='serif',  # Serif font for elegance
                   zorder=10)  # Ensure text appears on top

            # Adjust plot limits to accommodate text
            margin = self.height * 0.06  # Further reduced margin since text is very close
            ax.set_ylim(self.miny - margin, self.maxy)

        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Save the figure with error handling
        try:
            if background_color == 'transparent':
                plt.savefig(
                    output_path,
                    dpi=dpi,
                    bbox_inches='tight',
                    transparent=True,
                    edgecolor='none',
                    pad_inches=0.1
                )
            else:
                plt.savefig(
                    output_path,
                    dpi=dpi,
                    bbox_inches='tight',
                    facecolor=background_color,
                    edgecolor='none',
                    pad_inches=0.1
                )
            print(f"Design saved to: {output_path}")
        except Exception as e:
            raise IOError(f"Failed to save design to {output_path}: {e}")
        finally:
            plt.close()
    
    def batch_create_designs(self, mountain_name: str, output_folder: Union[str, Path], 
                           color_schemes: Optional[Dict[str, List[str]]] = None, 
                           name_suffix: str = "",
                           show_progress: bool = True,
                           **kwargs) -> List[Path]:
        """
        Create multiple versions with different color schemes.
        
        Args:
            mountain_name: Name to display on designs
            output_folder: Directory to save designs
            color_schemes: Dictionary of scheme names to color lists
            name_suffix: Suffix to add to filenames
            show_progress: Whether to show progress bar
            **kwargs: Additional arguments passed to create_block_design()
            
        Returns:
            List of paths to created files
            
        Raises:
            ValueError: If invalid color schemes provided
            IOError: If output folder cannot be created
        """
        if color_schemes is None:
            color_schemes = {
                # Monochrome schemes - excellent for screen printing
                'black': ['#1A1A1A', '#333333', '#4D4D4D'],
                'charcoal': ['#2C2C2C', '#404040', '#545454'],
                'white': ['#F5F5F5', '#E8E8E8', '#DBDBDB'],
                'navy': ['#1B2951', '#2C3E50', '#34495E'],

                # Muted earth tones - work well on fabric
                'desert': ['#8B7355', '#A0926B', '#B5A482'],
                'clay': ['#B85450', '#C67368', '#D49280'],
                'sage': ['#87A96B', '#9BB284', '#AFBC9C'],
                'stone': ['#7A7A7A', '#8C8C8C', '#9E9E9E'],

                # Tetradic complementary schemes (simplified to 3 colors)
                'autumn': ['#D2691E', '#8B4513', '#A0522D'],  # oranges/browns
                'forest': ['#228B22', '#2F4F2F', '#556B2F'],  # greens
                'ocean': ['#4682B4', '#5F9EA0', '#708090'],   # blue-grays
                'burgundy': ['#800020', '#9B2335', '#B6364A'], # deep reds

                # Single-color gradients (great for minimalist prints)
                'indigo': ['#2E3192', '#4B5F9B', '#688DA4'],
                'rust': ['#B7410E', '#C95A2A', '#DB7346'],
                'pine': ['#01796F', '#2D8B83', '#599D97'],
                'plum': ['#5D4037', '#6D4C41', '#795548']
            }
        
        # Validate color schemes
        for scheme_name, colors in color_schemes.items():
            if not isinstance(colors, list) or len(colors) != 3:
                raise ValueError(f"Color scheme '{scheme_name}' must have exactly 3 colors")
        
        output_folder = Path(output_folder)
        try:
            output_folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise IOError(f"Cannot create output folder {output_folder}: {e}")
        
        created_files = []
        
        # Create designs with progress tracking
        items = color_schemes.items()
        if show_progress:
            items = tqdm(items, desc=f"Creating {mountain_name} designs")
        
        for scheme_name, colors in items:
            safe_mountain_name = mountain_name.replace(' ', '_').replace('/', '_')
            filename = f"{safe_mountain_name}_{scheme_name}{name_suffix}.png"
            output_path = output_folder / filename
            
            try:
                self.create_block_design(mountain_name, output_path, colors, **kwargs)
                created_files.append(output_path)
            except Exception as e:
                warnings.warn(f"Failed to create {scheme_name} design: {e}")
                continue
        
        return created_files

# Utility functions
def process_mountain_design(contour_shapefile_path: Union[str, Path], 
                          mountain_name: str, 
                          output_folder: Union[str, Path],
                          border_shapefile_path: Optional[Union[str, Path]] = None,
                          **kwargs) -> List[Path]:
    """
    Process a single mountain design with all color schemes.
    
    Args:
        contour_shapefile_path: Path to contour shapefile
        mountain_name: Name to display on designs
        output_folder: Directory to save designs
        border_shapefile_path: Optional border shapefile
        **kwargs: Additional arguments for design creation
        
    Returns:
        List of created file paths
        
    Raises:
        FileNotFoundError: If contour shapefile doesn't exist
        ValueError: If shapefile is invalid
    """
    try:
        designer = TopoBlockDesigner(contour_shapefile_path, border_shapefile_path)
        return designer.batch_create_designs(mountain_name, output_folder, **kwargs)
    except Exception as e:
        print(f"Error processing {mountain_name}: {e}")
        return []

def batch_process_mountains(data_folder: Union[str, Path],
                          output_base_folder: Union[str, Path],
                          show_progress: bool = True,
                          **kwargs) -> Dict[str, List[Path]]:
    """
    Process multiple mountain designs from a structured folder.
    
    Expected folder structure:
    ```
    data_folder/
    ├── mountain1/
    │   ├── contours.shp (or any .shp file)
    │   └── border.shp (optional)
    ├── mountain2/
    │   ├── contours.shp
    │   └── border.shp (optional)
    ```
    
    Args:
        data_folder: Root folder containing mountain subfolders
        output_base_folder: Base folder for all outputs
        show_progress: Whether to show progress bars
        
    Returns:
        Dictionary mapping mountain names to lists of created files
        
    Raises:
        FileNotFoundError: If data folder doesn't exist
        ValueError: If folder structure is invalid
    """
    data_path = Path(data_folder)
    if not data_path.exists():
        raise FileNotFoundError(f"Data folder not found: {data_path}")
    
    if not data_path.is_dir():
        raise ValueError(f"Data path is not a directory: {data_path}")
    
    mountain_folders = [f for f in data_path.iterdir() if f.is_dir()]
    if not mountain_folders:
        raise ValueError(f"No mountain folders found in {data_path}")
    
    results = {}
    
    # Process each mountain folder
    folders = mountain_folders
    if show_progress:
        folders = tqdm(mountain_folders, desc="Processing mountains")
    
    for mountain_folder in folders:
        mountain_name = mountain_folder.name.replace('_', ' ').title()
        
        # Look for contour shapefile (prefer files with 'contour' in name)
        contour_files = list(mountain_folder.glob("*contour*.shp"))
        if not contour_files:
            contour_files = list(mountain_folder.glob("*.shp"))
        
        if not contour_files:
            warnings.warn(f"No shapefile found in {mountain_folder}")
            results[mountain_name] = []
            continue
            
        contour_path = contour_files[0]
        
        # Look for optional border shapefile
        border_files = list(mountain_folder.glob("*border*.shp"))
        border_path = border_files[0] if border_files else None
        
        # Create output folder
        output_folder = Path(output_base_folder) / mountain_folder.name
        
        try:
            created_files = process_mountain_design(
                contour_path, mountain_name, output_folder,
                border_path, show_progress=False,  # Individual progress handled above
                **kwargs
            )
            results[mountain_name] = created_files
            
            if show_progress:
                print(f"✓ {mountain_name}: {len(created_files)} designs created")
                
        except Exception as e:
            warnings.warn(f"Failed to process {mountain_name}: {e}")
            results[mountain_name] = []
    
    return results

def main():
    """
    Main function with example usage and CLI-like interface.
    Modify the paths below for your specific setup.
    """
    import argparse
    
    # Simple argument parsing for basic CLI functionality
    parser = argparse.ArgumentParser(description="Create topographic block designs")
    parser.add_argument("--contours", type=str, help="Path to contour shapefile")
    parser.add_argument("--border", type=str, help="Path to border shapefile (optional)")
    parser.add_argument("--name", type=str, help="Mountain name for display")
    parser.add_argument("--output", type=str, help="Output folder path")
    parser.add_argument("--batch", type=str, help="Batch process folder")
    parser.add_argument("--batch-output", type=str, help="Batch output base folder")
    parser.add_argument("--no-text", action="store_true", help="Don't display mountain name text")
    
    args = parser.parse_args()
    
    try:
        if args.batch and args.batch_output:
            # Batch processing mode
            print(f"Batch processing mountains from: {args.batch}")
            results = batch_process_mountains(args.batch, args.batch_output, show_text=not args.no_text)
            
            total_files = sum(len(files) for files in results.values())
            print(f"\n✅ Batch processing complete!")
            print(f"   Mountains processed: {len(results)}")
            print(f"   Total designs created: {total_files}")
            
            # Summary of results
            for mountain_name, files in results.items():
                if files:
                    print(f"   • {mountain_name}: {len(files)} designs")
                else:
                    print(f"   ⚠ {mountain_name}: Failed to create designs")
        
        elif args.contours and args.name and args.output:
            # Single mountain processing mode
            print(f"Processing {args.name}...")
            created_files = process_mountain_design(
                args.contours, args.name, args.output, args.border,
                show_text=not args.no_text
            )
            
            print(f"\n✅ Processing complete!")
            print(f"   Designs created: {len(created_files)}")
            for file_path in created_files:
                print(f"   • {file_path}")
        
        else:
            # Show example usage if no valid arguments provided
            print("🎨 Topographic Block Designer")
            print("=" * 40)
            print("\nExample usage:")
            print("\n1. Single mountain:")
            print("   python main.py --contours path/to/contours.shp --name 'Mt Adams' --output output/designs")
            print("   python main.py --contours contours.shp --border border.shp --name 'Mt Adams' --output output")
            
            print("\n2. Batch processing:")
            print("   python main.py --batch path/to/mountain_data --batch-output output/all_designs")
            
            print("\n3. Programmatic usage:")
            print("   # Uncomment and modify the example code below")
            print()
            
            # Example programmatic usage (commented out)
            example_single_processing = '''
    # Single mountain example
    try:
        contour_file = "input/mt_adams_contours.shp"
        mountain_name = "Mt Adams"
        output_folder = "output/mt_adams_designs"
        
        created_files = process_mountain_design(contour_file, mountain_name, output_folder)
        print(f"Created {len(created_files)} designs for {mountain_name}")
    except Exception as e:
        print(f"Error: {e}")
'''
            
            example_batch_processing = '''
    # Batch processing example
    try:
        results = batch_process_mountains("input/mountain_data", "output/all_designs")
        for mountain_name, files in results.items():
            print(f"{mountain_name}: {len(files)} designs created")
    except Exception as e:
        print(f"Batch processing error: {e}")
'''
            
            print("   # Example 1: Single mountain")
            for line in example_single_processing.strip().split('\n'):
                print(f"   {line}")
            
            print("\n   # Example 2: Batch processing")  
            for line in example_batch_processing.strip().split('\n'):
                print(f"   {line}")
                
            print("\n📁 Expected folder structure for batch processing:")
            print("   input/mountain_data/")
            print("   ├── mt_adams/")
            print("   │   ├── contours.shp")
            print("   │   └── border.shp (optional)")
            print("   ├── mt_rainier/")
            print("   │   └── contours.shp")
            print("   └── ...")
            
    except KeyboardInterrupt:
        print("\n\n⏹ Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
