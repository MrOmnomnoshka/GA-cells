import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Collectors;

public class Main {

    public static void main(String[] args) throws IOException {

        String fileNameSaveTo = args[0];
        String fileNameReadFrom = args[1];

        if (fileNameReadFrom.endsWith(".csv")) {
            String temp = fileNameSaveTo;
            fileNameSaveTo = fileNameReadFrom;
            fileNameReadFrom = temp;
        }
        String nodesStr = readStrFromFile(fileNameReadFrom);
        String[] splitedNodes = nodesStr.split("\n");

        List<String> splitedNodesList = List.of(splitedNodes);


        String str = splitedNodesList.parallelStream()
                .filter(s -> s.matches("^\\s+\\d+\\s+\\d+.\\d+\\s+\\d+.\\d+\\s+\\d+.\\d+\\s+"))
                .map(s -> s.strip().split("\\s+"))
                .sorted((o1, o2) -> Integer.valueOf(o1[0]).compareTo(Integer.valueOf(o2[0])))
                .map(parsedNode -> parsedNode[0] + "," + parsedNode[1] + "," + parsedNode[2] + "," + parsedNode[3])
                .collect(Collectors.joining("\n"));

        String header = "node_id,x,y,z" + System.lineSeparator();
        saveStringInFile(fileNameSaveTo, header, str);
    }

    private static String readStrFromFile(String fileName) throws IOException {
        return Files.readString(Path.of(fileName));
    }

    private static void saveStringInFile(String fileName, String  header, String str) throws IOException {
        BufferedWriter writer = new BufferedWriter(new FileWriter(fileName));
        writer.write(header);
        writer.write(str);
        writer.close();
    }

}
