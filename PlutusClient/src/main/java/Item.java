public class Item {
    private final String id;
    private int countReads;
    private int countWrites;
    private Byte[] value;
    private int placement;
    private boolean isFrozen;

    public Item (String id, Byte[] value) {
        this.id = id;
        this.value = value;
        countReads=0;
        countWrites=0;
        placement=0;
        isFrozen=false;
    }

    public String getId () {
        return id;
    }

    public int getCountReads () {
        return countReads;
    }

    public int getCountWrites () {
        return countWrites;
    }

    public int getPlacement () {
        return placement;
    }

    public void setPlacement (int placement) {
        this.placement = placement;
    }

    public Byte[] read() {
        countReads++;
        return value;
    }

    public void write(Byte[] newValue) {
        countWrites++;
        value = newValue;
    }

    public boolean freeze() {
        if(isFrozen)
            return false;
        isFrozen=true;
        return true;
    }

    public void unfreeze() {
        isFrozen=false;
    }


}
