// Select all header elements
const headers = document.querySelectorAll('.accordion-header');

headers.forEach(header => {
    header.addEventListener('click', () => {
        // Get the parent item (the .accordion-item div)
        const currentItem = header.parentElement;

        // Optional: Close all other items (Exclusive Accordion)
        document.querySelectorAll('.accordion-item').forEach(item => {
            if (item !== currentItem) {
                item.classList.remove('active');
                // Reset icon if you used specific text icons, CSS handles rotation
            }
        });

        // Toggle the clicked item
        currentItem.classList.toggle('active');
    });
});
