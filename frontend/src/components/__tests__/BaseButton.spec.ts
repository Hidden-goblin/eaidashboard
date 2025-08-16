import {describe, it, expect} from 'vitest';
import {mount} from '@vue/test-utils';
import BaseButton from '@/components/utils/BaseButton.vue';
import {RouterLinkStub} from '@vue/test-utils';

// Dummy icon to simulate a passed-in prop
const DummyIcon = {
    template: '<svg class="dummy-icon" />'
};

describe('BaseButton', () => {
    // 1. Render as a <button> when `to` is not provided
    it('renders as a <button> when "to" prop is not set', () => {
        const wrapper = mount(BaseButton, {
            slots: {default: 'Click me'}
        });

        // Check tag
        expect(wrapper.element.tagName).toBe('BUTTON');

        // Check base class
        expect(wrapper.classes()).toContain('btn-clear');

        // Check content
        expect(wrapper.text()).toBe('Click me');
    });

    // 2. Render as a <RouterLink> when "to" is provided
    it('renders as a <RouterLink> when "to" prop is set', () => {
        const wrapper = mount(BaseButton, {
            props: {to: '/home'},
            global: {
                stubs: {
                    RouterLink: RouterLinkStub
                }
            },
            slots: {default: 'Go home'}
        });

        expect(wrapper.findComponent(RouterLinkStub).exists()).toBe(true);
        expect(wrapper.findComponent(RouterLinkStub).props().to).toBe('/home');
    });

    // 3. Applies correct class based on "variant"
    it('applies correct class for the given variant', () => {
        const wrapper = mount(BaseButton, {
            props: {variant: 'delete'},
            slots: {default: 'Delete'}
        });

        expect(wrapper.classes()).toContain('btn-delete');
    });

    // 4. Falls back to "clear" variant if none is provided
    it('defaults to "clear" variant class', () => {
        const wrapper = mount(BaseButton, {
            slots: {default: 'Default button'}
        });

        expect(wrapper.classes()).toContain('btn-clear');
    });

    // 5. Uses icon prop if explicitly provided
    it('uses icon component passed via the "icon" prop', () => {
        const wrapper = mount(BaseButton, {
            props: {
                icon: DummyIcon
            },
            slots: {default: 'With icon'}
        });

        expect(wrapper.find('svg.dummy-icon').exists()).toBe(true);
    });

    // 6. Uses default icon when no icon prop is given but variant has one
    it('uses default icon based on "variant" if no icon prop is given', () => {
        const wrapper = mount(BaseButton, {
            props: {variant: 'create'},
            slots: {default: 'Create'}
        });

        // Should render a <svg> inside the icon span
        expect(wrapper.find('.icon svg').exists()).toBe(true);
    });

    // 7. Does not render an icon if neither "icon" prop nor variant has one
    it('does not render icon if variant and icon are missing', () => {
        const wrapper = mount(BaseButton, {
            props: {variant: 'clear'},
            slots: {default: 'No icon'}
        });

        expect(wrapper.find('.icon').exists()).toBe(false);
    });

    // 8. Passes native attributes like click event
    it('emits native events (click)', async () => {
        const wrapper = mount(BaseButton, {
            slots: {default: 'Click me'}
        });

        await wrapper.trigger('click');
        expect(wrapper.emitted('click')).toBeTruthy();
    });

    // 9. Passes through arbitrary attributes (like data-testid)
    it('forwards arbitrary attributes to the underlying element', () => {
        const wrapper = mount(BaseButton, {
            attrs: {'data-testid': 'my-button'},
            slots: {default: 'Attr test'}
        });

        expect(wrapper.attributes('data-testid')).toBe('my-button');
    });

    // 10. Accepts event listeners via props and triggers them
    it('calls event listeners passed via props', async () => {
        const onClick = vi.fn();

        const wrapper = mount(BaseButton, {
            attrs: {onClick}, // simulate v-on:click
            slots: {default: 'Click handler test'}
        });

        await wrapper.trigger('click');
        expect(onClick).toHaveBeenCalled();
    });
});
