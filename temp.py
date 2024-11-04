import numpy as np
from numba import cuda, njit


# Define the CUDA kernel
@cuda.jit
def double_elements_kernel(array):
    idx = cuda.grid(1)
    if idx < array.size:
        array[idx] *= 2  # Double the element


# Define an njit function that launches the CUDA kernel
@njit
def launch_kernel_on_device(array_device, array_size):
    threads_per_block = 32
    blocks_per_grid = (array_size + (threads_per_block - 1)) // threads_per_block

    # Launch the CUDA kernel
    double_elements_kernel[blocks_per_grid, threads_per_block](array_device)
    cuda.synchronize()  # Ensure all threads finish execution


# Define an njit function that calls the kernel-launching njit function
@njit
def process_array(array):
    # Transfer array to the GPU
    array_device = cuda.to_device(array)

    # Launch the CUDA operation through the kernel-launching function
    launch_kernel_on_device(array_device, array.size)

    # Copy result back to the host
    result = array_device.copy_to_host()
    return result


# Main function to run the script
def main():
    # Initialize data
    data = np.array([1, 2, 3, 4, 5], dtype=np.float32)
    print("Original array:", data)

    # Process the array using the njit functions and CUDA kernel
    processed_data = process_array(data)

    print("Processed array (doubled):", processed_data)


if __name__ == "__main__":
    main()
